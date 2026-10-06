#!/usr/bin/env python3
"""
Verifie que toutes les actions dans les workflows GitHub Actions sont
pinnées à un commit SHA.
Usage: python check_action_pinning.py
"""

import re
import sys
from pathlib import Path

# Construit le chemin dynamiquement depuis l'emplacement du script
WORKFLOWS_DIR = Path(__file__).parent.parent.parent / "workflows"

# Pattern pour detecter une action avec un tag (non pinnee)
# Exemple: uses: actions/checkout@v4  ou  uses: actions/checkout@main
NON_PINNED_PATTERN = re.compile(
    r"uses:\s*[^\s]+@(?!([0-9a-fA-F]{40}|[0-9a-fA-F]{64})\b)"
)


def check_workflow_file(file_path: Path) -> list[str]:
    """Verifie qu'un fichier workflow a toutes ses actions pinnees."""
    errors = []
    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
        for line_num, line in enumerate(content.splitlines(), 1):
            if "uses:" in line and NON_PINNED_PATTERN.search(line):
                # Extraire le nom de l'action
                match = re.search(r"uses:\s*([^\s#]+)", line)
                if match:
                    action_ref = match.group(1)
                    errors.append(
                        f"{file_path}:{line_num} - Action non pinnee: {action_ref}"
                    )
    except (UnicodeDecodeError, PermissionError):
        errors.append(f"Erreur de lecture: {file_path}")
    return errors


def main():
    """Verifie tous les workflows."""
    all_errors = []

    if not WORKFLOWS_DIR.exists():
        print("[OK] Dossier .github/workflows/ introuvable - rien a verifier")
        sys.exit(0)

    for workflow_file in WORKFLOWS_DIR.glob("*.yml"):
        errors = check_workflow_file(workflow_file)
        all_errors.extend(errors)

    if all_errors:
        print("[ERREUR] Actions non pinnees detectees :")
        for error in all_errors:
            print(f"   -> {error}")
        sys.exit(1)
    else:
        print("[OK] Toutes les actions sont pinnees a un commit SHA.")
        sys.exit(0)


if __name__ == "__main__":
    main()
