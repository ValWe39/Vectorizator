"""Tests unitaires de vectorizator.checkpoint (T024)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from vectorizator.checkpoint import checkpoint_path, load, remove, save

VECTORS = [[1.0, 2.0], [3.0, 4.0]]


def test_sauvegarde_et_chargement(tmp_path: Path) -> None:
    out = tmp_path / "out"
    source = tmp_path / "doc.json"
    save(out, source, "mistral-embed", 25, VECTORS)
    assert checkpoint_path(out, source).exists()
    vectors, invalide = load(out, source, "mistral-embed", 25)
    assert vectors == VECTORS
    assert invalide is False


def test_absent_sans_invalidation(tmp_path: Path) -> None:
    out = tmp_path / "out"
    vectors, invalide = load(out, tmp_path / "doc.json", "mistral-embed", 25)
    assert vectors == []
    assert invalide is False


def test_invalidation_si_modele_different(tmp_path: Path) -> None:
    """Changement de modèle : checkpoint invalidé (clarification Q3)."""
    out = tmp_path / "out"
    source = tmp_path / "doc.json"
    save(out, source, "mistral-embed", 25, VECTORS)
    vectors, invalide = load(out, source, "mistral-embed-dim256-2510", 25)
    assert vectors == []
    assert invalide is True


def test_invalidation_si_taille_de_lot_different(tmp_path: Path) -> None:
    """La taille de lot change les découpages : invalidation aussi."""
    out = tmp_path / "out"
    source = tmp_path / "doc.json"
    save(out, source, "mistral-embed", 25, VECTORS)
    vectors, invalide = load(out, source, "mistral-embed", 50)
    assert vectors == []
    assert invalide is True


def test_invalidation_si_corrompu(tmp_path: Path) -> None:
    out = tmp_path / "out"
    source = tmp_path / "doc.json"
    path = checkpoint_path(out, source)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{ pas du json", encoding="utf-8")
    vectors, invalide = load(out, source, "mistral-embed", 25)
    assert vectors == []
    assert invalide is True


def test_suppression_apres_succes(tmp_path: Path) -> None:
    """Le checkpoint est supprimé dès que la matrice est produite (Q4)."""
    out = tmp_path / "out"
    source = tmp_path / "doc.json"
    save(out, source, "mistral-embed", 25, VECTORS)
    remove(out, source)
    assert not checkpoint_path(out, source).exists()
    # Supprimer un checkpoint absent ne lève pas d'erreur.
    remove(out, source)


def test_enrichissement_par_lot(tmp_path: Path) -> None:
    """Chaque lot réussi enrichit le checkpoint dans l'ordre (FR-009)."""
    out = tmp_path / "out"
    source = tmp_path / "doc.json"
    for tour, vecteur in enumerate([[9.0], [8.0], [7.0]]):
        save(out, source, "mistral-embed", 1, [[9.0], [8.0], [7.0]][: tour + 1])
    vectors, _ = load(out, source, "mistral-embed", 1)
    assert vectors == [[9.0], [8.0], [7.0]]


def test_nom_d_input_sanitise(tmp_path: Path) -> None:
    out = tmp_path / "out"
    source = tmp_path / "nom:avec*interdits.json"
    path = checkpoint_path(out, source)
    assert path.parent == out / ".checkpoints"
    assert path.name == "nom_avec_interdits.json.json"


def test_payload_structure(tmp_path: Path) -> None:
    out = tmp_path / "out"
    source = tmp_path / "doc.json"
    save(out, source, "mistral-embed", 25, VECTORS)
    payload = json.loads(checkpoint_path(out, source).read_text(encoding="utf-8"))
    assert set(payload) == {"model", "batch_size", "vectors"}
    assert payload["model"] == "mistral-embed"
    assert payload["batch_size"] == 25


@pytest.mark.parametrize("vectors", [None, "pas une liste", 42])
def test_payload_vectors_invalide(tmp_path: Path, vectors: object) -> None:
    out = tmp_path / "out"
    source = tmp_path / "doc.json"
    path = checkpoint_path(out, source)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"model": "m", "batch_size": 25, "vectors": vectors}),
        encoding="utf-8",
    )
    _, invalide = load(out, source, "m", 25)
    assert invalide is True
