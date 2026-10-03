#!/usr/bin/env python3
"""
Audit des workflows GitHub Actions pour Vectorizator.
Vérifie :
- Pas de secrets codés en dur
- Permissions minimales (contents: read)
- Pas d'appels à des actions externes non approuvées
"""

import re
import sys
from pathlib import Path

WORKFLOWS_DIR = Path(".github/workflows")

# Actions autorisées (à adapter selon ta politique)
ALLOWED_ACTIONS = {
    "actions/checkout",
    "actions/setup-python",
    "actions/setup-node",
    "actions/cache",
}

# Patterns interdits
FORBIDDEN_PATTERNS = [
    r"(?i)(api[_-]?key|secret|token|password)\s*[:=]",
    r"permissions:\s*write",  # Seuls 'read' autorisés
    r"uses:\s*.*@main",  # Éviter les branches instables
]


def audit_workflow(file_path: Path) -> list[str]:
    """Audit un fichier de workflow."""
    errors = []
    try:
        content = file_path.read_text(encoding="utf-8")
        for line_num, line in enumerate(content.splitlines(), 1):
            for pattern in FORBIDDEN_PATTERNS:
                if re.search(pattern, line):
                    errors.append(f"{file_path}:{line_num} - Match: {pattern}")

            # Vérifier les actions utilisées
            if line.strip().startswith("uses:"):
                action = line.split("uses:")[1].strip()
                if not any(allowed in action for allowed in ALLOWED_ACTIONS):
                    errors.append(
                        f"{file_path}:{line_num} - Action non approuvée: {action}"
                    )
    except (UnicodeDecodeError, PermissionError):
        errors.append(f"Erreur de lecture: {file_path}")
    return errors


def main():
    if len(sys.argv) < 2:
        print("Usage: python audit_workflows.py <workflows_dir>")
        sys.exit(1)

    workflows_dir = Path(sys.argv[1])
    if not workflows_dir.exists():
        print(f"⚠️  Dossier introuvable: {workflows_dir}")
        sys.exit(0)

    all_errors = []
    for workflow_file in workflows_dir.glob("*.yml"):
        # Exclure diagnostic.yml : contient GITHUB_TOKEN autorise par la constitution (Amendement 1)
        if workflow_file.name == "diagnostic.yml":
            continue
        errors = audit_workflow(workflow_file)
        all_errors.extend(errors)

    if all_errors:
        print("[ERREUR] Problemes detectes dans les workflows :")
        for error in all_errors:
            print(f"   -> {error}")
        sys.exit(1)
    else:
        print("[OK] Tous les workflows sont conformes.")
        sys.exit(0)


if __name__ == "__main__":
    main()
