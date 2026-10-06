"""Détection et collecte des inputs (US2, FR-001, FR-002, data-model §1).

Un input peut être un fichier, plusieurs fichiers ou un dossier — la
nature est détectée automatiquement, sans option dédiée. Dans un
dossier, seuls les fichiers .json sont retenus (les autres sont
ignorés), dans l'ordre alphabétique stable (assumption de la spec).
"""

from __future__ import annotations

from pathlib import Path


class InputsError(Exception):
    """Chemin d'input introuvable."""


def collect_inputs(paths: list[str]) -> list[Path]:
    """Collecte les fichiers .json à traiter depuis les chemins donnés.

    - Fichier : retenu tel quel (validé plus tard par le schéma).
    - Dossier : seuls les fichiers .json du premier niveau, triés.
    - Chemin inexistant : InputsError (échec rapide).
    """
    collected: list[Path] = []
    for raw in paths:
        path = Path(raw)
        if not path.exists():
            raise InputsError(f"chemin introuvable : {raw}")
        if path.is_dir():
            found = [
                item
                for item in path.iterdir()
                if item.is_file() and item.suffix.lower() == ".json"
            ]
            collected.extend(sorted(found))
        else:
            collected.append(path)
    return collected
