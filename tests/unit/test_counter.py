"""Tests unitaires de vectorizator.counter (T011)."""

from __future__ import annotations

from pathlib import Path

import pytest

from vectorizator.counter import (
    COUNTER_FILENAME,
    CounterError,
    counter_path,
    next_occurrence,
    read_counter,
)


def test_premier_usage_0001_quand_absent(tmp_path: Path) -> None:
    """Fichier absent -> repart à 0001 (FR-013, FR-011)."""
    assert next_occurrence(tmp_path) == "0001"
    assert counter_path(tmp_path).read_text(encoding="utf-8") == "0001"


def test_increment_et_persistance(tmp_path: Path) -> None:
    """Progression d'une unité, persistée après chaque document (FR-011)."""
    counter_path(tmp_path).write_text("0041", encoding="utf-8")
    assert next_occurrence(tmp_path) == "0042"
    assert counter_path(tmp_path).read_text(encoding="utf-8") == "0042"
    assert next_occurrence(tmp_path) == "0043"


def test_cycle_9999_puis_0000_puis_0001(tmp_path: Path) -> None:
    """Cycle imposé : 0001..9999 -> 0000 -> 0001 (FR-012)."""
    counter_path(tmp_path).write_text("9998", encoding="utf-8")
    assert next_occurrence(tmp_path) == "9999"
    assert next_occurrence(tmp_path) == "0000"
    assert next_occurrence(tmp_path) == "0001"


def test_corrompu_echoue_rapidement(tmp_path: Path) -> None:
    """Illisible/corrompu : échec explicite, rien n'est écrit (FR-013)."""
    counter_path(tmp_path).write_text("abcd", encoding="utf-8")
    with pytest.raises(CounterError, match="corrompu"):
        next_occurrence(tmp_path)
    assert counter_path(tmp_path).read_text(encoding="utf-8") == "abcd"


@pytest.mark.parametrize("contenu", ["42", "12345", "", "-1  ", "00 42"])
def test_formats_invalides_rejetes(contenu: str, tmp_path: Path) -> None:
    counter_path(tmp_path).write_text(contenu, encoding="utf-8")
    with pytest.raises(CounterError):
        next_occurrence(tmp_path)


def test_aucun_numero_reutilise_sur_serie(tmp_path: Path) -> None:
    """Sur une série d'usages, aucun numéro ne se répète (SC-005)."""
    vus = {next_occurrence(tmp_path) for _ in range(10)}
    assert len(vus) == 10


def test_read_counter(tmp_path: Path) -> None:
    assert read_counter(tmp_path) is None
    next_occurrence(tmp_path)
    assert read_counter(tmp_path) == "0001"


def test_nom_de_fichier_reference(tmp_path: Path) -> None:
    assert counter_path(tmp_path).name == COUNTER_FILENAME
