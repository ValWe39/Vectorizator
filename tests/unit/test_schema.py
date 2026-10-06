"""Tests unitaires de vectorizator.schema (T008)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from vectorizator.schema import SchemaError, validate_index

DATA_DIR = Path(__file__).parent.parent / "data"

_UNSET = object()


def build_index(
    schema_version: str = "1.0",
    title: object = "Titre de test",
    chunks: object = _UNSET,
) -> dict:
    if chunks is _UNSET:
        chunks = [{"ref": 1, "text": "Premier chunk de texte."}]
    return {
        "schema_version": schema_version,
        "document": {"title": title},
        "params": {},
        "chunks": chunks,
    }


def test_index_valide_fixture_reelle() -> None:
    """Le fixture sample_index.json passe et preserve l'ordre des chunks."""
    data = json.loads((DATA_DIR / "sample_index.json").read_text(encoding="utf-8"))
    title, texts = validate_index(data, "sample_index.json")
    assert title == "Introduction aux Embeddings"
    assert len(texts) == 5
    assert texts[0].startswith("Un embedding")
    assert texts[4].startswith("Deux textes")


def test_index_valide_minimal() -> None:
    title, texts = validate_index(build_index(), "x.json")
    assert title == "Titre de test"
    assert texts == ["Premier chunk de texte."]


@pytest.mark.parametrize(
    "data",
    [
        "une chaîne",
        [1, 2, 3],
        None,
    ],
)
def test_index_non_objet(data: object) -> None:
    with pytest.raises(SchemaError, match="objet"):
        validate_index(data, "x.json")


def test_schema_version_invalide() -> None:
    with pytest.raises(SchemaError, match="schema_version"):
        validate_index(build_index(schema_version="2.0"), "x.json")


def test_titre_vide() -> None:
    with pytest.raises(SchemaError, match="title"):
        validate_index(build_index(title="   "), "x.json")


def test_titre_absent_accepte() -> None:
    """Title optionnel : un JSON sans document.title est valide
    (exemple réel 016492360000000016.json, 2026-10-06)."""
    data = {
        "schema_version": "1.0",
        "document": {"path": "x.md"},
        "chunks": [{"ref": 1, "text": "texte"}],
    }
    title, texts = validate_index(data, "x.json")
    assert title is None
    assert texts == ["texte"]


@pytest.mark.parametrize(
    "chunks",
    [
        [],
        "pas une liste",
        None,
    ],
)
def test_chunks_invalides(chunks: object) -> None:
    with pytest.raises(SchemaError, match="chunks"):
        validate_index(build_index(chunks=chunks), "x.json")


def test_chunk_sans_text() -> None:
    chunks = [{"ref": 1, "text": "   "}, {"ref": 2, "text": "ok"}]
    with pytest.raises(SchemaError, match="chunk 1"):
        validate_index(build_index(chunks=chunks), "x.json")


def test_chunk_ref_non_entier() -> None:
    chunks = [{"ref": "1", "text": "texte"}]
    with pytest.raises(SchemaError, match="ref"):
        validate_index(build_index(chunks=chunks), "x.json")


def test_message_contient_le_chemin_d_input() -> None:
    with pytest.raises(SchemaError, match=r"\[mon-fichier\.json\]"):
        validate_index({"schema_version": "1.0"}, "mon-fichier.json")
