"""Test d'intégration US4 : effets des options CLI (T032)."""

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
        return fake

    monkeypatch.setattr("vectorizator.cli.make_client", _factory)


def prepare(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, fake: FakeClient):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("MISTRAL_API_KEY", "cle-de-test-fictive")
    install_fake_client(monkeypatch, fake)


def test_choix_techno_256_colonnes(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Scénario 3 du quickstart : 256 colonnes avec le preset 256."""
    prepare(monkeypatch, tmp_path, FakeClient(dim=256))
    out = tmp_path / "out"
    code = main(
        [
            str(DATA),
            "--output-folder",
            str(out),
            "--choix-techno",
            "mistral-embed-dim256-2510",
        ]
    )
    assert code == EXIT_OK
    matrix = np.load(next(out.glob("*.npy")))
    assert matrix.shape == (5, 256)
    # Le nom du modèle passé à l'API est exactement celui du preset.
    # (vérifié via fake.calls dans le test 128 ci-dessous)


def test_choix_techno_128_colonnes_et_nom_d_appel(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    fake = FakeClient(dim=128)
    prepare(monkeypatch, tmp_path, fake)
    out = tmp_path / "out"
    code = main(
        [
            str(DATA),
            "--output-folder",
            str(out),
            "--choix-techno",
            "mistral-embed-dim128-2510",
        ]
    )
    assert code == EXIT_OK
    assert fake.calls[0][0] == "mistral-embed-dim128-2510"
    matrix = np.load(next(out.glob("*.npy")))
    assert matrix.shape == (5, 128)


def test_default_1024_colonnes(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Sans option : mistral-embed, 1024 dimensions (FR-006)."""
    fake = FakeClient(dim=1024)
    prepare(monkeypatch, tmp_path, fake)
    out = tmp_path / "out"
    code = main([str(DATA), "--output-folder", str(out)])
    assert code == EXIT_OK
    assert fake.calls[0][0] == "mistral-embed"
    matrix = np.load(next(out.glob("*.npy")))
    assert matrix.shape == (5, 1024)


def test_taille_batch_zero_requetes_simples(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Scénario 4 du quickstart : 0 = pas de batch, une requête par chunk."""
    fake = FakeClient(dim=1024)
    prepare(monkeypatch, tmp_path, fake)
    out = tmp_path / "out"
    code = main([str(DATA), "--output-folder", str(out), "--taille-batch", "0"])
    assert code == EXIT_OK
    # 5 chunks -> 5 requêtes simples, une par chunk.
    assert len(fake.calls) == 5
    assert all(len(inputs) == 1 for _, inputs in fake.calls)
    # Matrice complète et ordonnée : ligne i <-> chunk i, chaque chunk
    # étant l'appel i (encodage i * 10000).
    matrix = np.load(next(out.glob("*.npy")))
    assert matrix.shape == (5, 1024)
    assert [matrix[i][0] for i in range(5)] == [0.0, 10000.0, 20000.0, 30000.0, 40000.0]


def test_output_folder_alternatif_cree(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """--output-folder : dossier alternatif créé si absent (FR-014)."""
    prepare(monkeypatch, tmp_path, FakeClient(dim=1024))
    cible = tmp_path / "profonde" / "mes_sorties"
    code = main([str(DATA), "--output-folder", str(cible)])
    assert code == EXIT_OK
    assert cible.is_dir()
    assert len(list(cible.glob("*.npy"))) == 1


def test_output_folder_defaut_output_sous_cwd(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Sans option : dossier `output` à la racine du projet (cwd)."""
    prepare(monkeypatch, tmp_path, FakeClient(dim=1024))
    code = main([str(DATA)])
    assert code == EXIT_OK
    out = tmp_path / "output"
    assert out.is_dir()
    assert len(list(out.glob("*.npy"))) == 1
    assert (tmp_path / COUNTER_FILENAME).exists()
