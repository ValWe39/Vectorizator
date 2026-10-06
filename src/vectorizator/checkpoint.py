"""État de reprise persistant par document (R-06, data-model §7, FR-009).

Un fichier JSON par document en cours sous
`<output>/.checkpoints/<nom d'input sanitisé>.json`, contenant le
modèle, la taille de lot et les vecteurs des lots déjà réussis, dans
l'ordre. Supprimé dès que la matrice est écrite avec succès.
"""

from __future__ import annotations

import json
from pathlib import Path

from vectorizator.output import sanitize_name

CHECKPOINT_DIRNAME = ".checkpoints"


def checkpoint_path(output_dir: Path, source: Path) -> Path:
    """Chemin du checkpoint d'un document sous le dossier de sortie."""
    name = sanitize_name(Path(source).name)
    return output_dir / CHECKPOINT_DIRNAME / f"{name}.json"


def save(
    output_dir: Path,
    source: Path,
    model: str,
    batch_size: int,
    vectors: list[list[float]],
) -> None:
    """Persiste l'état de reprise après chaque lot réussi (FR-009)."""
    path = checkpoint_path(output_dir, source)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"model": model, "batch_size": batch_size, "vectors": vectors}
    path.write_text(json.dumps(payload), encoding="utf-8")


def load(
    output_dir: Path,
    source: Path,
    model: str,
    batch_size: int,
) -> tuple[list[list[float]], bool]:
    """Charge l'état de reprise ; retourne (vecteurs, invalide).

    - Checkpoint absent : ([], False) — traitement normal.
    - Modèle ou taille de lot différents, ou fichier corrompu :
      ([], True) — l'appelant affiche l'avertissement d'invalidation
      et re-vectorise depuis le premier lot (clarification Q3).
    """
    path = checkpoint_path(output_dir, source)
    if not path.exists():
        return [], False
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        vectors = payload["vectors"]
        if not isinstance(vectors, list):
            raise ValueError("vectors doit être une liste")
    except (json.JSONDecodeError, KeyError, TypeError, ValueError, OSError):
        return [], True
    if payload.get("model") != model or payload.get("batch_size") != batch_size:
        return [], True
    return vectors, False


def remove(output_dir: Path, source: Path) -> None:
    """Supprime le checkpoint après succès de la matrice (clarification Q4)."""
    checkpoint_path(output_dir, source).unlink(missing_ok=True)
