"""Tests unitaires de vectorizator.cli : bornes et codes de sortie (T008)."""

from __future__ import annotations

import pytest

from vectorizator.cli import (
    EXIT_CONFIG,
    CliError,
    build_parser,
    main,
    validate_args,
)


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
