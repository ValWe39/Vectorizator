"""Test d'intégration US1 : un JSON -> une matrice ordonnée (T015)."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from tests.fakes import FakeClient
from vectorizator.cli import EXIT_OK, main
from vectorizator.counter import COUNTER_FILENAME

DATA = Path(__file__).resolve().parents[1] / "data" / "sample_index.json"


def install_fake_client(monkeypatch: pytest.MonkeyPatch, fake: FakeClient) -> None:
    def _factory(api_key: str) -> FakeClient:
        assert api_key, "la clé API doit être transmise au client"
        return fake

    monkeypatch.setattr("vectorizator.cli.make_client", _factory)


def test_pipeline_mono_document(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Scénario 1 du quickstart : JSON unique -> matrice ordonnée."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("MISTRAL_API_KEY", "cle-de-test-fictive")
    fake = FakeClient(dim=1024)
    install_fake_client(monkeypatch, fake)
    out = tmp_path / "out"

    code = main([str(DATA), "--output-folder", str(out)])

    assert code == EXIT_OK
    files = sorted(out.glob("*.npy"))
    assert len(files) == 1
    # FR-010 : 18 premiers caractères du nom de fichier (stem).
    assert files[0].name == "sample_index-0001.npy"
    matrix = np.load(files[0])
    assert matrix.shape == (5, 1024)
    assert matrix.dtype == np.float32
    # FR-005 : ligne i <-> chunk i (FakeClient encode la position).
    assert matrix[0][0] == 0.0
    assert matrix[2][0] == 2.0
    assert matrix[4][0] == 4.0
    # FR-011 : compteur persisté après le document produit.
    assert (tmp_path / COUNTER_FILENAME).read_text(encoding="utf-8") == "0001"
    # Un seul appel API, tous les chunks dans l'ordre d'envoi.
    assert len(fake.calls) == 1
    assert len(fake.calls[0][1]) == 5


def test_deuxieme_document_numeros_consecutifs(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Relancer le même JSON produit un nouveau numéro (clarification Q1)."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("MISTRAL_API_KEY", "cle-de-test-fictive")
    install_fake_client(monkeypatch, FakeClient(dim=1024))
    out = tmp_path / "out"

    assert main([str(DATA), "--output-folder", str(out)]) == EXIT_OK
    assert main([str(DATA), "--output-folder", str(out)]) == EXIT_OK

    names = sorted(p.name for p in out.glob("*.npy"))
    assert names == [
        "sample_index-0001.npy",
        "sample_index-0002.npy",
    ]
    assert (tmp_path / COUNTER_FILENAME).read_text(encoding="utf-8") == "0002"


def test_json_invalide_echec_document_exit_2(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """JSON non conforme : échec du document, message explicite (FR-016)."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("MISTRAL_API_KEY", "cle-de-test-fictive")
    install_fake_client(monkeypatch, FakeClient(dim=1024))
    bad = tmp_path / "bad.json"
    bad.write_text('{"schema_version": "2.0"}', encoding="utf-8")

    code = main([str(bad), "--output-folder", str(tmp_path / "out")])

    assert code == 2
    assert not list((tmp_path / "out").glob("*.npy"))
    # Aucun numéro consommé pour un document non produit.
    assert not (tmp_path / COUNTER_FILENAME).exists()
