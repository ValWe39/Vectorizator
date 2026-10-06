"""Validation du schema JSON d'index 1.0 (R-10, data-model §1-2)."""

from __future__ import annotations

from typing import Any

SCHEMA_VERSION = "1.0"


class SchemaError(Exception):
    """JSON d'index invalide ou non conforme au schema 1.0."""


def validate_index(data: Any, source: str) -> tuple[str | None, list[str]]:
    """Valide un JSON d'index ; retourne (titre optionnel, textes).

    L'ordre de la liste retournee est l'ordre des chunks du fichier :
    il fixe l'ordre des lignes de la matrice (FR-005).
    Les autres champs (length, boundary, part, page, position_in_part,
    atomic, params) sont lus sans être interprétés.
    """
    where = f"[{source}] "
    if not isinstance(data, dict):
        msg = "le JSON doit être un objet."
        raise SchemaError(where + msg)
    version = data.get("schema_version")
    if version != SCHEMA_VERSION:
        msg = f"schema_version doit valoir '1.0' (reçu : {version!r})."
        raise SchemaError(where + msg)
    document = data.get("document")
    if not isinstance(document, dict):
        msg = "document doit être un objet."
        raise SchemaError(where + msg)
    title = document.get("title")
    if title is not None and (not isinstance(title, str) or not title.strip()):
        msg = "document.title, s'il est présent, doit être une chaîne non vide."
        raise SchemaError(where + msg)
    chunks = data.get("chunks")
    if not isinstance(chunks, list) or not chunks:
        msg = "chunks doit être une liste non vide."
        raise SchemaError(where + msg)
    texts: list[str] = []
    for position, chunk in enumerate(chunks, start=1):
        if not isinstance(chunk, dict):
            msg = f"chunk {position} : doit être un objet."
            raise SchemaError(where + msg)
        ref = chunk.get("ref")
        if isinstance(ref, bool) or not isinstance(ref, int):
            msg = f"chunk {position} : ref doit être un entier."
            raise SchemaError(where + msg)
        text = chunk.get("text")
        if not isinstance(text, str) or not text.strip():
            msg = f"chunk {position} : text doit être une chaîne non vide."
            raise SchemaError(where + msg)
        texts.append(text)
    return title, texts
