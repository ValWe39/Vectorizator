"""Test d'intégration US3 : batch, retry et reprise (T026)."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from tests.fakes import FakeClient, FakeHTTPError
from vectorizator.checkpoint import checkpoint_path
from vectorizator.cli import EXIT_DOC_FAILURE, EXIT_OK, main
from vectorizator.counter import COUNTER_FILENAME

TITLE = "Document de test reprise"


def write_index(path: Path, nb_chunks: int) -> None:
    chunks = [{"ref": i, "text": f"chunk numéro {i}"} for i in range(1, nb_chunks + 1)]
    path.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "document": {"title": TITLE},
                "chunks": chunks,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def install_fake_client(monkeypatch: pytest.MonkeyPatch, fake: FakeClient) -> None:
    def _factory(api_key: str) -> FakeClient:
        return fake

    monkeypatch.setattr("vectorizator.cli.make_client", _factory)


def test_reprise_apres_echec_du_troisieme_lot(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Échec au 3e lot -> reprise sans renvoyer les lots 1 et 2 (SC-003)."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("MISTRAL_API_KEY", "cle-de-test-fictive")
    out = tmp_path / "out"
    doc = tmp_path / "gros.json"
    write_index(doc, nb_chunks=12)  # 3 lots de 5 : 5 + 5 + 2

    # Échec : lot 3 (appel 2) en 429, 1 seul retry aussi en échec.
    failant = FakeClient(
        dim=1024,
        failures={2: [FakeHTTPError(429)], 3: [FakeHTTPError(429)]},
    )
    install_fake_client(monkeypatch, failant)
    code = main(
        [
            str(doc),
            "--output-folder",
            str(out),
            "--taille-batch",
            "5",
            "--retry-occurences",
            "1",
            "--retry-time",
            "1",
        ]
    )
    assert code == EXIT_DOC_FAILURE
    assert not list(out.glob("*.npy"))
    # Le checkpoint contient les 10 vecteurs des lots 1 et 2.
    cp = checkpoint_path(out, doc)
    assert cp.exists()
    payload = json.loads(cp.read_text(encoding="utf-8"))
    assert len(payload["vectors"]) == 10
    # Aucun numéro consommé (aucune matrice produite).
    assert not (tmp_path / COUNTER_FILENAME).exists()

    # Reprise : seuls les lots restants sont renvoyés à l'API.
    reprenant = FakeClient(dim=1024)
    install_fake_client(monkeypatch, reprenant)
    code = main(
        [
            str(doc),
            "--output-folder",
            str(out),
            "--taille-batch",
            "5",
            "--retry-occurences",
            "1",
            "--retry-time",
            "1",
        ]
    )
    assert code == EXIT_OK
    # Un seul appel : le lot 3 (2 chunks), pas les lots 1 et 2.
    assert len(reprenant.calls) == 1
    assert len(reprenant.calls[0][1]) == 2
    # Matrice complète et ordonnée : 12 lignes.
    files = list(out.glob("*.npy"))
    assert len(files) == 1
    matrix = np.load(files[0])
    assert matrix.shape == (12, 1024)
    # Les lots 1-2 viennent du checkpoint (encodage du premier run),
    # le lot 3 est le premier appel du run de reprise (encodage 0, 1).
    assert matrix[9][0] == 10000.0 + 4.0  # dernier vecteur du lot 2 (appel 1)
    assert matrix[10][0] == 0.0
    assert matrix[11][0] == 1.0
    # Checkpoint supprimé après succès (clarification Q4).
    assert not cp.exists()
    assert (tmp_path / COUNTER_FILENAME).read_text(encoding="utf-8") == "0001"


def test_invalidation_du_checkpoint_si_modele_change(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Modèle différent à la reprise : tout est re-vectorisé (Q3)."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("MISTRAL_API_KEY", "cle-de-test-fictive")
    out = tmp_path / "out"
    doc = tmp_path / "gros.json"
    write_index(doc, nb_chunks=12)

    failant = FakeClient(
        dim=1024, failures={2: [FakeHTTPError(500)], 3: [FakeHTTPError(500)]}
    )
    install_fake_client(monkeypatch, failant)
    main(
        [
            str(doc),
            "--output-folder",
            str(out),
            "--taille-batch",
            "5",
            "--retry-occurences",
            "0",
        ]
    )
    assert checkpoint_path(out, doc).exists()

    # Reprise avec un autre modèle : 3 appels complets, avertissement.
    reprenant = FakeClient(dim=256)
    install_fake_client(monkeypatch, reprenant)
    code = main(
        [
            str(doc),
            "--output-folder",
            str(out),
            "--taille-batch",
            "5",
            "--retry-occurences",
            "1",
            "--choix-techno",
            "mistral-embed-dim256-2510",
        ]
    )
    assert code == EXIT_OK
    # Tous les lots sont renvoyés (invalidation du checkpoint).
    assert len(reprenant.calls) == 3
    files = list(out.glob("*.npy"))
    matrix = np.load(files[0])
    assert matrix.shape == (12, 256)


def test_checkpoint_absent_sans_evenement(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Succès sans échec : le checkpoint n'existe plus après traitement."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("MISTRAL_API_KEY", "cle-de-test-fictive")
    out = tmp_path / "out"
    doc = tmp_path / "petit.json"
    write_index(doc, nb_chunks=3)
    install_fake_client(monkeypatch, FakeClient(dim=1024))

    code = main([str(doc), "--output-folder", str(out), "--taille-batch", "2"])

    assert code == EXIT_OK
    assert not checkpoint_path(out, doc).exists()
    assert len(list(out.glob("*.npy"))) == 1
