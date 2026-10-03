#!/usr/bin/env python3
"""
Vérifie la conformité à la constitution de [OUTIL].
Usage:
  python check_constitution.py          # Vérifie tout le repo
  python check_constitution.py --diff HEAD~1  # Vérifie uniquement les modifications

Note: Les scripts de vérification (check_constitution.py, audit_workflows.py) sont
      exclus des checks pour éviter les faux positifs (ex: détection de mots-clés
      comme 'cloud' ou 'tracking' dans leur propre code alors qu'ils vérifient
      justement l'absence de ces éléments).
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path

# --- CONSTANTES ---
CONSTITUTION_PATH = Path(".specify/memory/constitution.md")
ALLOWED_PLACEHOLDERS = {
    "YOUR_API_KEY",
    "DATA_DIR",
    "YOUR_TOKEN",
    "YOUR_SECRET",
    "PLACEHOLDER",
}

# Fichiers à exclure des vérifications pour éviter les faux positifs
# (ex: le script check_constitution.py contient le mot "cloud" dans CLOUD_SERVICES)
# (ex: la constitution documentent les règles, donc contient les termes interdits)
# (ex: check_action_pinning.py vérifie les actions, donc contient des références aux workflows)
EXCLUDED_FILES = {
    Path(".github/workflows/scripts/check_constitution.py"),
    Path(".github/workflows/scripts/audit_workflows.py"),
    Path(".specify/memory/constitution.md"),
    Path(".github/workflows/scripts/check_action_pinning.py"),
}

CLOUD_SERVICES = {
    "aws",
    "amazon",
    "s3",
    "ec2",
    "lambda",
    "firebas",
    "google.*cloud",
    "gcp",
    "azure",
    "heroku",
    "vercel",
    "netlify",
    "sendgrid",
    "mailgun",
    "stripe",
    "analytics",
    "telemetry",
    "tracking",
    "crashlytics",
    "sentry",
    "mixpanel",
}


# --- FONCTIONS DE VÉRIFICATION ---
def get_diff_files(ref: str) -> set[Path]:
    """Récupère les fichiers modifiés depuis `ref`."""
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", ref],
            capture_output=True,
            text=True,
            check=True,
        )
        return {Path(f) for f in result.stdout.splitlines() if f}
    except subprocess.CalledProcessError:
        return set()


def check_no_hardcoded_secrets(files: set[Path] | None = None) -> list[str]:
    """Règle I : Aucune clé API/token codée en dur."""
    errors = []
    patterns = [
        r"(?i)(api[_-]?key|secret[_-]?key|access[_-]?token|auth[_-]?token|password|private[_-]?key)\s*[:=]\s*['\"]([^'\"]+)[\"']",
        r"(?i)(api[_-]?key|token|secret)\s*[:=]\s*[A-Za-z0-9\-_]{20,}",
    ]
    files_to_check = files if files else set(Path(".").rglob("*"))
    for pattern in patterns:
        for file_path in files_to_check:
            if not file_path.is_file() or file_path in EXCLUDED_FILES:
                continue
            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                for match in re.finditer(pattern, content):
                    value = match.group(1) if match.groups() else match.group(0)
                    if not any(ph in value for ph in ALLOWED_PLACEHOLDERS):
                        line_num = content.count("\n", 0, match.start()) + 1
                        errors.append(f"{file_path}:{line_num}")
            except (UnicodeDecodeError, PermissionError):
                continue
    return errors


def check_no_cloud_services(files: set[Path] | None = None) -> list[str]:
    """Règle II : Interdiction des services cloud."""
    errors = []
    cloud_pattern = re.compile(r"(?i)(" + "|".join(CLOUD_SERVICES) + r")")
    files_to_check = files if files else set(Path(".").rglob("*.py"))
    for file_path in files_to_check:
        if not file_path.is_file() or file_path in EXCLUDED_FILES:
            continue
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            if cloud_pattern.search(content):
                errors.append(f"{file_path} (services cloud détectés)")
        except (UnicodeDecodeError, PermissionError):
            continue
    return errors


def check_no_trackers(files: set[Path] | None = None) -> list[str]:
    """Règle : Interdiction des trackers/télémétrie."""
    errors = []
    tracker_keywords = [
        "analytics",
        "telemetry",
        "tracking",
        "sentry",
        "mixpanel",
        "amplitude",
    ]
    files_to_check = files if files else set(Path(".").rglob("*.py"))
    for file_path in files_to_check:
        if not file_path.is_file() or file_path in EXCLUDED_FILES:
            continue
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            if any(keyword.lower() in content.lower() for keyword in tracker_keywords):
                errors.append(f"{file_path} (mots-clés de tracking détectés)")
        except (UnicodeDecodeError, PermissionError):
            continue
    return errors


def check_no_hardcoded_paths(files: set[Path] | None = None) -> list[str]:
    """Règle : Pas de chemins codés en dur."""
    errors = []
    path_patterns = [
        r"(?i)[A-Za-z]:\\",  # Chemins absolus Windows
        r"/home/[\w/]+",  # Chemins utilisateur Linux
        r"/Users/[\w/]+",  # Chemins utilisateur macOS
    ]
    files_to_check = files if files else set(Path(".").rglob("*.py"))
    for pattern in path_patterns:
        for file_path in files_to_check:
            if not file_path.is_file() or file_path in EXCLUDED_FILES:
                continue
            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                if re.search(pattern, content):
                    errors.append(f"{file_path} (chemins codés en dur détectés)")
            except (UnicodeDecodeError, PermissionError):
                continue
    return errors


def check_gitignore_coverage() -> list[str]:
    """Vérifie que .gitignore couvre les éléments requis."""
    errors = []
    gitignore_path = Path(".gitignore")
    if not gitignore_path.exists():
        return ["Le fichier .gitignore est manquant"]
    gitignore_content = gitignore_path.read_text()
    required_patterns = [".env", "input/", "output/", "Prompts/", ".vibe/"]
    for pattern in required_patterns:
        if pattern not in gitignore_content:
            errors.append(f".gitignore ne couvre pas : {pattern}")
    return errors


def check_license_exists() -> list[str]:
    """Vérifie que le fichier LICENSE existe."""
    return [] if Path("LICENSE").exists() else ["Le fichier LICENSE est manquant"]


def check_constitution_exists() -> list[str]:
    """Vérifie que la constitution existe."""
    return [] if CONSTITUTION_PATH.exists() else [f"{CONSTITUTION_PATH} introuvable"]


# --- EXÉCUTION ---
def main():
    parser = argparse.ArgumentParser(
        description="Vérifier la conformité à la constitution."
    )
    parser.add_argument(
        "--diff",
        metavar="REF",
        help="Vérifier uniquement les modifications depuis REF (ex: HEAD~1)",
    )
    args = parser.parse_args()

    print("[CONSTITUTION] Verification de la constitution [OUTIL]...")

    files_to_check = None
    if args.diff:
        files_to_check = get_diff_files(args.diff)
        print(f"-> Mode diff : verification des fichiers modifies depuis {args.diff}")

    all_errors = []

    checks = [
        ("constitution_exists", check_constitution_exists, False),
        ("gitignore_coverage", check_gitignore_coverage, False),
        ("license_exists", check_license_exists, False),
        ("no_hardcoded_secrets", check_no_hardcoded_secrets, True),
        ("no_cloud_services", check_no_cloud_services, True),
        ("no_trackers", check_no_trackers, True),
        ("no_hardcoded_paths", check_no_hardcoded_paths, True),
    ]

    for check_name, check_func, use_files in checks:
        try:
            if use_files and files_to_check:
                errors = check_func(files_to_check)
            else:
                errors = check_func()
            if errors:
                print(f"[ERREUR] Regle '{check_name}' violee :")
                for error in errors:
                    print(f"   -> {error}")
                all_errors.extend(errors)
        except (OSError, ValueError, subprocess.CalledProcessError) as e:
            all_errors.append(f"Erreur dans {check_name}: {e!s}")

    if all_errors:
        print(f"\n[ERREUR] {len(all_errors)} violation(s) detectee(s).")
        sys.exit(1)
    else:
        print("[OK] Toutes les regles de la constitution sont respectees.")
        sys.exit(0)


if __name__ == "__main__":
    main()
