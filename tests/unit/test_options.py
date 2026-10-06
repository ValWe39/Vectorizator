"""Tests unitaires du câblage des options CLI (T027, US4).

Vérifie que chaque option, avec une valeur valide, atterrit dans le
namespace avec la bonne clé, et que les défauts sont ceux du contrat
(contracts/cli-contract.md).
"""

from __future__ import annotations

from vectorizator.cli import build_parser, validate_args


def parse(argv: list[str]):
    return build_parser().parse_args(argv)


def test_choix_techno_atterrit_correctement() -> None:
    for model in (
        "mistral-embed",
        "mistral-embed-dim256-2510",
        "mistral-embed-dim128-2510",
    ):
        args = parse(["a.json", "--choix-techno", model])
        assert args.choix_techno == model
        validate_args(args)


def test_taille_batch_valeur_custom() -> None:
    args = parse(["a.json", "--taille-batch", "100"])
    assert args.taille_batch == 100
    validate_args(args)


def test_retry_options_valeurs_custom() -> None:
    args = parse(["a.json", "--retry-occurences", "10", "--retry-time", "10"])
    assert args.retry_occurences == 10
    assert args.retry_time == 10
    validate_args(args)


def test_output_folder_valeur_custom() -> None:
    args = parse(["a.json", "--output-folder", "mes_vecteurs"])
    assert args.output_folder == "mes_vecteurs"
    validate_args(args)


def test_optionscombinees() -> None:
    argv = [
        "a.json",
        "b.json",
        "--choix-techno",
        "mistral-embed-dim128-2510",
        "--taille-batch",
        "0",
        "--retry-occurences",
        "5",
        "--retry-time",
        "2",
        "--output-folder",
        "sorties",
    ]
    args = parse(argv)
    assert args.inputs == ["a.json", "b.json"]
    assert args.choix_techno == "mistral-embed-dim128-2510"
    assert args.taille_batch == 0
    assert args.retry_occurences == 5
    assert args.retry_time == 2
    assert args.output_folder == "sorties"
    validate_args(args)


def test_defauts_du_contrat() -> None:
    """Les défauts restent ceux du contrat (contracts/cli-contract.md)."""
    defaults = parse(["a.json"])
    assert defaults.choix_techno == "mistral-embed"
    assert defaults.taille_batch == 25
    assert defaults.retry_occurences == 3
    assert defaults.retry_time == 3
    assert defaults.output_folder == "output"
