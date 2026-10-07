"""Tests unitaires de vectorizator.cli : bornes et codes de sortie (T008 ;
T002/T008/T010, option --rapport)."""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.fakes import FakeClient
from vectorizator.cli import (
    EXIT_CONFIG,
    EXIT_DOC_FAILURE,
    EXIT_OK,
    CliError,
    build_parser,
    main,
    validate_args,
)
from vectorizator.counter import COUNTER_FILENAME

DATA = Path(__file__).resolve().parents[1] / "data" / "sample_index.json"


def parse_args(argv: list[str]):
    return build_parser().parse_args(argv)


def test_valeurs_par_defaut_du_contrat() -> None:
    """Defauts du contrat CLI : mistral-embed, 25, 3, 3 s, output."""
    args = parse_args(["a.json"])
    assert args.choix_techno == "mistral-embed"
    assert args.taille_batch == 25
    assert args.retry_occurences == 3
    assert args.retry_time == 3
    assert args.output_folder == "output"


def test_bornes_valides_aux_limites() -> None:
    args = parse_args(
        [
            "a.json",
            "--taille-batch",
            "0",
            "--retry-occurences",
            "0",
            "--retry-time",
            "1",
        ]
    )
    validate_args(args)


@pytest.mark.parametrize(
    "argv",
    [
        ["a.json", "--choix-techno", "modele-factice"],
        ["a.json", "--taille-batch", "150"],
        ["a.json", "--taille-batch", "-1"],
        ["a.json", "--retry-occurences", "11"],
        ["a.json", "--retry-time", "0"],
    ],
)
def test_bornes_invalides_rejetees(argv: list[str]) -> None:
    args = parse_args(argv)
    with pytest.raises(CliError):
        validate_args(args)


def test_main_bornes_invalides_exit_1(capsys: pytest.CaptureFixture) -> None:
    """Valeur hors bornes : echec rapide, message explicite, code 1 (FR-016)."""
    code = main(["a.json", "--taille-batch", "150"])
    assert code == EXIT_CONFIG
    assert "--taille-batch" in capsys.readouterr().err


# --- Feature --rapport (T002, T008, T010) ---


def test_rapport_desactive_par_defaut() -> None:
    """SC-002/FR-001 : sans --rapport, le flag est inactif."""
    args = parse_args(["a.json"])
    assert args.rapport is False


def test_rapport_active_par_le_flag() -> None:
    """FR-001 : la présence de --rapport active le flag, sans valeur."""
    args = parse_args(["a.json", "--rapport"])
    assert args.rapport is True


def test_main_bornes_invalides_avec_rapport_exit_1(
    capsys: pytest.CaptureFixture,
) -> None:
    """FR-012 : --rapport ne change pas l'échec rapide de validation."""
    code = main(["a.json", "--rapport", "--taille-batch", "150"])
    assert code == EXIT_CONFIG
    assert "--taille-batch" in capsys.readouterr().err


def test_rapport_non_ecrit_document_en_echec(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """FR-011 : échec d'écriture du rapport -> échec documentaire.

    La matrice déjà écrite est conservée, le checkpoint reste en place
    (reprise possible), le code de sortie est 2 (research.md R-05).
    """
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("MISTRAL_API_KEY", "cle-de-test-fictive")
    fake = FakeClient(dim=1024)

    def _factory(api_key: str) -> FakeClient:
        assert api_key, "la clé API doit être transmise au client"
        return fake

    monkeypatch.setattr("vectorizator.cli.make_client", _factory)

    def _report_failure(
        source: Path, matrix_path: Path, model: str, dimension: int
    ) -> Path:
        raise OSError("disque plein simulé")

    monkeypatch.setattr("vectorizator.cli.save_report", _report_failure)
    out = tmp_path / "out"

    code = main([str(DATA), "--output-folder", str(out), "--rapport"])

    assert code == EXIT_DOC_FAILURE
    # Matrice conservée, aucun rapport, checkpoint conservé.
    assert [p.name for p in out.glob("*.npy")] == ["sample_index-0001.npy"]
    assert not list(out.glob("*.json"))
    assert list((out / ".checkpoints").glob("*.json"))
    # Le numéro d'occurrence a bien été consommé pour la matrice.
    assert (tmp_path / COUNTER_FILENAME).read_text(encoding="utf-8") == "0001"


def test_rapport_ok_code_sortie_0(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """SC-002 : avec --rapport et succès, le code de sortie reste 0."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("MISTRAL_API_KEY", "cle-de-test-fictive")

    def _factory(api_key: str) -> FakeClient:
        assert api_key, "la clé API doit être transmise au client"
        return FakeClient(dim=1024)

    monkeypatch.setattr("vectorizator.cli.make_client", _factory)
    out = tmp_path / "out"

    code = main([str(DATA), "--output-folder", str(out), "--rapport"])

    assert code == EXIT_OK
    assert [p.name for p in out.glob("*.json")] == ["sample_index-0001.json"]
