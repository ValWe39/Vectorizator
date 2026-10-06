"""Configuration : cle API et presets de modeles d'embedding (R-02, R-03)."""

from __future__ import annotations

import os

from dotenv import load_dotenv

MODELS: dict[str, int] = {
    "mistral-embed": 1024,
    "mistral-embed-dim256-2510": 256,
    "mistral-embed-dim128-2510": 128,
}
DEFAULT_MODEL = "mistral-embed"


class ConfigError(Exception):
    """Erreur de configuration (cle absente, modele inconnu)."""


def load_api_key() -> str:
    """Charge MISTRAL_API_KEY depuis le .env ou l'environnement.

    Echoue rapidement si absente ou vide (Constitution I, FR-015/FR-016).
    La cle n'est jamais affichee ni ecrite par cette fonction.
    """
    load_dotenv()
    key = os.environ.get("MISTRAL_API_KEY", "")
    if not key:
        msg = (
            "MISTRAL_API_KEY absente ou vide : définissez-la dans le "
            "fichier .env (voir .env.example) ou dans l'environnement."
        )
        raise ConfigError(msg)
    return key


def model_dimension(model: str) -> int:
    """Retourne la dimension du preset, ou échoue si le modele est inconnu."""
    try:
        return MODELS[model]
    except KeyError:
        accepted = ", ".join(sorted(MODELS))
        msg = f"Modèle inconnu : {model!r} (acceptés : {accepted})."
        raise ConfigError(msg) from None
