"""Compteur d'occurrence persistant (R-07, data-model §6, FR-011 à FR-013).

Le fichier counter.txt vit à la racine de l'outil (répertoire courant
d'exécution) et contient uniquement le dernier numéro consommé.
"""

from __future__ import annotations

from pathlib import Path

COUNTER_FILENAME = "counter.txt"
_CYCLE_MAX = 9999


class CounterError(Exception):
    """Compteur illisible ou corrompu : échec rapide, sans écrire de sortie."""


def counter_path(root: Path) -> Path:
    """Chemin du fichier compteur sous la racine donnée."""
    return root / COUNTER_FILENAME


def _format(value: int) -> str:
    return f"{value:04d}"


def _parse(content: str) -> int:
    """Exige exactement 4 chiffres ; sinon le compteur est corrompu."""
    text = content.strip()
    if len(text) != 4 or not text.isdigit():
        extrait = content.strip()[:50] or "(vide)"
        msg = (
            f"Le fichier compteur {COUNTER_FILENAME!r} est illisible ou "
            f"corrompu (contenu : {extrait!r}). Corrigez-le en écrivant "
            "un numéro à 4 chiffres, puis relancez."
        )
        raise CounterError(msg)
    return int(text)


def next_occurrence(root: Path) -> str:
    """Attribue le numéro suivant, le persiste et le retourne.

    Fichier absent -> premier usage à 0001 (FR-013). Cycle : progression
    d'une unité par document, 9999 -> 0000 -> 0001 (FR-012). Le numéro
    est persisté immédiatement, avant l'écriture de la matrice : un
    numéro consommé n'est jamais réutilisé, même en cas d'interruption
    (FR-011).
    """
    path = counter_path(root)
    if path.exists():
        current = _parse(path.read_text(encoding="utf-8"))
        nxt = 0 if current == _CYCLE_MAX else current + 1
    else:
        nxt = 1
    formatted = _format(nxt)
    path.write_text(formatted, encoding="utf-8")
    return formatted


def read_counter(root: Path) -> str | None:
    """Retourne le dernier numéro consommé, ou None si le fichier est absent."""
    path = counter_path(root)
    if not path.exists():
        return None
    return _format(_parse(path.read_text(encoding="utf-8")))
