"""Tests unitaires de vectorizator.config (T008)."""

from __future__ import annotations

import pytest

from vectorizator.config import (
    DEFAULT_MODEL,
    MODELS,
    ConfigError,
    load_api_key,
    model_dimension,
)


def _sans_dotenv() -> None:
    """Neutralise le chargement du .env pour isoler l'environnement."""
    return None


def test_presets_complets() -> None:
    """Mapping des trois modeles imposes par la spec (FR-006)."""
    assert MODELS == {
        "mistral-embed": 1024,
        "mistral-embed-dim256-2510": 256,
        "mistral-embed-dim128-2510": 128,
    }
    assert DEFAULT_MODEL == "mistral-embed"


@pytest.mark.parametrize(
    ("model", "dimension"),
    [
        ("mistral-embed", 1024),
        ("mistral-embed-dim256-2510", 256),
        ("mistral-embed-dim128-2510", 128),
    ],
)
def test_model_dimension(model: str, dimension: int) -> None:
    assert model_dimension(model) == dimension


def test_model_dimension_inconnu() -> None:
    with pytest.raises(ConfigError, match="Modèle inconnu"):
        model_dimension("mistral-embed-42")


def test_load_api_key_absente(monkeypatch: pytest.MonkeyPatch) -> None:
    """Cle absente ou vide : echec rapide avant tout appel reseau (FR-016)."""
    monkeypatch.delenv("MISTRAL_API_KEY", raising=False)
    monkeypatch.setattr("vectorizator.config.load_dotenv", _sans_dotenv)
    with pytest.raises(ConfigError, match="MISTRAL_API_KEY"):
        load_api_key()


def test_load_api_key_presente(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MISTRAL_API_KEY", "cle-de-test-fictive")
    monkeypatch.setattr("vectorizator.config.load_dotenv", _sans_dotenv)
    assert load_api_key() == "cle-de-test-fictive"
