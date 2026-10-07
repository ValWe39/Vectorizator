"""Tests d'intégration de l'option --rapport (T004, T011).

Client SDK simulé via tests.fakes.FakeClient — aucun réseau.
"""

from __future__ import annotations

import json
from pathlib import Path

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


def _run_with_rapport(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, argv: list[str]
) -> int:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("MISTRAL_API_KEY", "cle-de-test-fictive")
    install_fake_client(monkeypatch, FakeClient(dim=1024))
    return main(argv)


def test_rapport_option_produit_sidecar(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Scénario 1 du quickstart : --rapport -> matrice + rapport."""
    out = tmp_path / "out"

    code = _run_with_rapport(
        monkeypatch, tmp_path, [str(DATA), "--output-folder", str(out), "--rapport"]
    )

    assert code == EXIT_OK
    npy_files = sorted(out.glob("*.npy"))
    json_files = sorted(out.glob("*.json"))
    assert [p.name for p in npy_files] == ["sample_index-0001.npy"]
    assert [p.name for p in json_files] == ["sample_index-0001.json"]
    rapport = json.loads(json_files[0].read_text(encoding="utf-8"))
    assert rapport == {
        "entrée": "sample_index.json",
        "sortie": "sample_index-0001.npy",
        "embed": "mistral-embed",
        "dimension": 1024,
        "nature": "float32",
    }
    # Même numéro d'occurrence entre matrice et rapport (FR-003).
    assert (tmp_path / COUNTER_FILENAME).read_text(encoding="utf-8") == "0001"


def test_sans_rapport_aucun_json(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Scénario 2 du quickstart : sans --rapport, aucun fichier .json."""
    out = tmp_path / "out"

    code = _run_with_rapport(
        monkeypatch, tmp_path, [str(DATA), "--output-folder", str(out)]
    )

    assert code == EXIT_OK
    assert len(list(out.glob("*.npy"))) == 1
    assert not list(out.glob("*.json"))


def test_lot_echec_partiel_rapports_uniquement_pour_reussites(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Scénario 4 du quickstart (T011) : un JSON valide + un invalide.

    FR-008 : le document en échec ne produit ni matrice ni rapport ;
    le document valide reçoit les deux ; code de sortie 2.
    """
    lot = tmp_path / "lot"
    lot.mkdir()
    valid = lot / "sample_index.json"
    valid.write_text(DATA.read_text(encoding="utf-8"), encoding="utf-8")
    (lot / "bad.json").write_text('{"schema_version": "2.0"}', encoding="utf-8")
    out = tmp_path / "out"

    code = _run_with_rapport(
        monkeypatch, tmp_path, [str(lot), "--output-folder", str(out), "--rapport"]
    )

    assert code == 2
    assert [p.name for p in out.glob("*.npy")] == ["sample_index-0001.npy"]
    assert [p.name for p in out.glob("*.json")] == ["sample_index-0001.json"]
