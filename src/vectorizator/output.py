"""Nommage et sauvegarde des matrices de sortie (R-08, data-model §5).

Le nom de sortie reprend les 18 premiers caractères du nom de fichier
du JSON d'entrée, sans son extension (« stem »), sanitisés — et non le
champ document.title (fix titre-depuis-nom-json, 2026-10-06).

Feature --rapport : sidecar JSON de traçabilité par matrice
(data-model.md §1 du feature 002, research.md R-01 à R-03).
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np

# Caractères interdits dans un nom de fichier Windows/Linux/macOS,
# remplacés par '_' ; les espaces sont conservés (R-08).
_FORBIDDEN = re.compile(r'[/\\:*?"<>|\x00-\x1f]')

# Nombre de caractères du nom de fichier repris dans le nom de sortie.
NAME_LENGTH = 18


def sanitize_name(name: str) -> str:
    """Neutralise les caractères interdits en nom de fichier."""
    return _FORBIDDEN.sub("_", name)


def build_output_name(source_stem: str, occurrence: str) -> str:
    """Nom de sortie : stem tronqué à 18 caractères + numéro (FR-010).

    source_stem est le nom de fichier du JSON d'entrée sans extension ;
    l'extension `.json` n'apparaît jamais dans le nom de sortie.
    """
    return f"{sanitize_name(source_stem)[:NAME_LENGTH]}-{occurrence}.npy"


def save_matrix(
    output_dir: Path,
    source_stem: str,
    occurrence: str,
    vectors: list[list[float]],
) -> Path:
    """Écrit la matrice float32 dans le dossier de sortie (créé si absent).

    L'ordre des lignes DOIT être l'ordre des chunks : l'appelant fournit
    les vecteurs déjà assemblés dans cet ordre (extend, FR-005).
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / build_output_name(source_stem, occurrence)
    matrix = np.asarray(vectors, dtype=np.float32)
    np.save(path, matrix)
    return path


def save_report(
    source: Path,
    matrix_path: Path,
    model: str,
    dimension: int,
) -> Path:
    """Écrit le sidecar JSON de traçabilité de la matrice (FR-003/FR-004).

    Le rapport porte le même nom que la matrice, extension `.json`,
    dérivé du chemin construit par `build_output_name` — jamais
    recalculé indépendamment (research.md R-02). Les cinq champs
    reflètent l'exécution réelle : « nature » est le dtype de la
    matrice écrite, lu depuis le fichier (research.md R-03). UTF-8,
    indentation 2, retour à la ligne final (research.md R-01) ; jamais
    de chemin absolu ni de clé (FR-005, FR-009).
    """
    report = {
        "entrée": source.name,
        "sortie": matrix_path.name,
        "embed": model,
        "dimension": dimension,
        "nature": np.load(matrix_path).dtype.name,
    }
    path = matrix_path.with_suffix(".json")
    path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return path
