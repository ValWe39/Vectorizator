"""Appels à l'API Mistral Embeddings : batching, retry, reprise (US3).

Décisions de research.md : R-01 (SDK sync), R-04 (lots, ordre par
extend), R-05 (retry uniquement sur erreurs transitoires).
"""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import Protocol


class EmbeddingError(Exception):
    """Échec définitif du document (erreur définitive ou essais épuisés)."""


class EmbeddingsClient(Protocol):
    """Interface minimale du client SDK (client.embeddings.create)."""

    def create(self, model: str, inputs: list[str]) -> object:  # pragma: no cover
        ...


def is_transient(exc: Exception) -> bool:
    """Classe une erreur d'appel : transitoire (True) ou définitive (False).

    Transitoire (R-05) : timeout, erreur réseau (sans code HTTP), 429
    (saturation), 5xx (erreur serveur). Définitive : 4xx hors 429
    (clé invalide, requête rejetée) — retenter masquerait la cause.
    """
    status = getattr(exc, "status_code", None)
    if isinstance(status, int):
        return status == 429 or status >= 500
    return True


def _embed_batch(
    client: EmbeddingsClient,
    model: str,
    batch: list[str],
    batch_index: int,
    expected_dimension: int,
    retry_occurrences: int,
    retry_time: int,
    sleep: Callable[[float], object],
) -> list[list[float]]:
    """Envoie un lot avec retry exponentiel ; retourne ses vecteurs."""
    attempt = 0
    while True:
        try:
            response = client.embeddings.create(model=model, inputs=list(batch))
            break
        except Exception as exc:  # noqa: BLE001 - classification ci-dessous
            if not is_transient(exc):
                status = getattr(exc, "status_code", "?")
                msg = (
                    f"lot {batch_index + 1} : erreur définitive (HTTP {status}) : {exc}"
                )
                raise EmbeddingError(msg) from exc
            if attempt >= retry_occurrences:
                msg = (
                    f"lot {batch_index + 1} : échec après "
                    f"{retry_occurrences} essai(s) de retry : {exc}"
                )
                raise EmbeddingError(msg) from exc
            delay = float(retry_time) * (2**attempt)
            sleep(delay)
            attempt += 1
    data = list(getattr(response, "data"))
    if len(data) != len(batch):
        msg = (
            f"lot {batch_index + 1} : l'API a renvoyé {len(data)} vecteurs "
            f"pour {len(batch)} textes envoyés."
        )
        raise EmbeddingError(msg)
    vectors: list[list[float]] = []
    for position, item in enumerate(data):
        vector = list(item.embedding)
        if len(vector) != expected_dimension:
            msg = (
                f"lot {batch_index + 1} : dimension inattendue pour le "
                f"vecteur {position} : {len(vector)} (attendu : "
                f"{expected_dimension} pour {model!r})."
            )
            raise EmbeddingError(msg)
        vectors.extend([vector])
    return vectors


def embed_texts(
    client: EmbeddingsClient,
    model: str,
    texts: list[str],
    expected_dimension: int,
    batch_size: int = 25,
    retry_occurrences: int = 3,
    retry_time: int = 3,
    *,
    skip_batches: int = 0,
    on_batch_done: Callable[[list[list[float]]], object] | None = None,
    sleep: Callable[[float], object] = time.sleep,
) -> list[list[float]]:
    """Vectorise tous les textes par lots ; ordre ligne i <-> chunk i.

    - batch_size : chunks par lot (FR-007) ; 0 = requête simple par
      chunk, sans regroupement.
    - skip_batches : nombre de lots déjà réussis (reprise) : ils ne
      sont PAS renvoyés à l'API (FR-009).
    - on_batch_done : appelé après chaque lot réussi avec l'accumulation
      complète, pour persister l'état de reprise.
    """
    size = batch_size if batch_size > 0 else 1
    vectors: list[list[float]] = []
    for batch_index, start in enumerate(range(0, len(texts), size)):
        if batch_index < skip_batches:
            continue
        batch = texts[start : start + size]
        batch_vectors = _embed_batch(
            client,
            model,
            batch,
            batch_index,
            expected_dimension,
            retry_occurrences,
            retry_time,
            sleep,
        )
        vectors.extend(batch_vectors)
        if on_batch_done is not None:
            on_batch_done(vectors)
    return vectors
