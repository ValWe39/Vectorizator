"""Test d'intégration US2 : multi-input et dossiers (T019)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests.fakes import FakeClient
from vectorizator.cli import EXIT_CONFIG, EXIT_DOC_FAILURE, EXIT_OK, main
from vectorizator.counter import COUNTER_FILENAME

DATA = Path(__file__).resolve().parents[1] / "data" / "sample_index.json"


def install_fake_client(monkeypatch: pytest.MonkeyPatch, fake: FakeClient) -> None:
    def _factory(api_key: str) -> FakeClient:
        return fake

    monkeypatch.setattr("vectorizator.cli.make_client", _factory)


def write_index(path: Path, title: str) -> None:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    data["document"]["title"] = title
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


@pytest.fixture()
def dossier_de_documents(tmp_path: Path) -> Path:
    """4 JSON valides + 2 fichiers non-JSON, comme le scénario 2."""
    dossier = tmp_path / "corpus"
    dossier.mkdir()
    for i in range(4):
        write_index(dossier / f"doc{i}.json", f"Document numéro {i}")
    (dossier / "notes.txt").write_text("ignorer", encoding="utf-8")
    (dossier / "brouillon.md").write_text("# brouillon", encoding="utf-8")
    return dossier


def test_dossier_complet_quatre_matrices(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, dossier_de_documents: Path
) -> None:
    """Scénario 2 : 4 JSON -> 4 matrices, numéros consécutifs (SC-002)."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("MISTRAL_API_KEY", "cle-de-test-fictive")
    fake = FakeClient(dim=1024)
    install_fake_client(monkeypatch, fake)
    out = tmp_path / "out"

    code = main([str(dossier_de_documents), "--output-folder", str(out)])

    assert code == EXIT_OK
    files = sorted(out.glob("*.npy"))
    assert len(files) == 4
    # Numéros consécutifs sans doublon, dans l'ordre de traitement.
    occurrences = sorted(f.name.rsplit("-", 1)[1] for f in files)
    assert occurrences == ["0001.npy", "0002.npy", "0003.npy", "0004.npy"]
    assert (tmp_path / COUNTER_FILENAME).read_text(encoding="utf-8") == "0004"


def test_echec_d_un_document_n_interrompt_pas_les_suivants(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """FR-003 : échec d'un JSON indépendant des autres ; exit 2 partiel."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("MISTRAL_API_KEY", "cle-de-test-fictive")
    install_fake_client(monkeypatch, FakeClient(dim=1024))
    out = tmp_path / "out"
    write_index(tmp_path / "bon1.json", "Bon un")
    (tmp_path / "mauvais.json").write_text(
        '{"schema_version": "9.9"}', encoding="utf-8"
    )
    write_index(tmp_path / "bon2.json", "Bon deux")

    code = main(
        [
            str(tmp_path / "mauvais.json"),
            str(tmp_path / "bon1.json"),
            str(tmp_path / "bon2.json"),
            "--output-folder",
            str(out),
        ]
    )

    assert code == EXIT_DOC_FAILURE
    # Les deux documents valides ont été produits.
    assert len(list(out.glob("*.npy"))) == 2
    assert (tmp_path / COUNTER_FILENAME).read_text(encoding="utf-8") == "0002"


def test_dossier_sans_json_aucun_numero_consomme(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Scénario US2-3 : aucun input traitable, message, rien de consommé."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("MISTRAL_API_KEY", "cle-de-test-fictive")
    install_fake_client(monkeypatch, FakeClient(dim=1024))
    vide = tmp_path / "vide"
    vide.mkdir()
    (vide / "readme.txt").write_text("vide", encoding="utf-8")

    code = main([str(vide), "--output-folder", str(tmp_path / "out")])

    assert code == EXIT_CONFIG
    assert not (tmp_path / "out").exists()
    assert not (tmp_path / COUNTER_FILENAME).exists()
