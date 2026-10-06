"""Tests unitaires du retry exponentiel et du batching (T020, T022)."""

from __future__ import annotations

import pytest

from tests.fakes import FakeClient, FakeHTTPError
from vectorizator.embedder import EmbeddingError, embed_texts, is_transient


class RecordingSleep:
    """Sleep injecté : enregistre les délais sans attendre réellement."""

    def __init__(self) -> None:
        self.delays: list[float] = []

    def __call__(self, seconds: float) -> None:
        self.delays.append(seconds)


def embed(fake, texts, **kwargs):
    """Raccourci : embed_texts avec valeurs par défaut du contrat."""
    defaults = {
        "expected_dimension": fake.dim,
        "batch_size": 25,
        "retry_occurrences": 3,
        "retry_time": 3,
        "sleep": RecordingSleep(),
    }
    defaults.update(kwargs)
    return embed_texts(fake, "mistral-embed", texts, **defaults), defaults["sleep"]


# --- Classification transitoire / définitive (R-05) ---


@pytest.mark.parametrize(
    ("status", "transitoire"),
    [(429, True), (500, True), (503, True), (401, False), (404, False)],
)
def test_is_transient_par_code_http(status: int, transitoire: bool) -> None:
    assert is_transient(FakeHTTPError(status)) is transitoire


def test_is_transient_sans_code_http() -> None:
    """Sans code HTTP (réseau, timeout) : transitoire (R-05)."""
    assert is_transient(TimeoutError("timeout")) is True


# --- Retry exponentiel (FR-008) ---


def test_delais_doubles_3_6_12() -> None:
    """Configuration par défaut : 3 essais aux délais 3, 6 et 12 s."""
    fake = FakeClient(dim=4, failures={i: [FakeHTTPError(429)] for i in range(3)})
    vectors, sleep = embed(fake, ["a"])
    assert sleep.delays == [3.0, 6.0, 12.0]
    # 1 appel initial + 3 retries.
    assert len(fake.calls) == 4
    # Le vecteur vient du 4e appel (indice 3) : la réponse a réussi.
    assert vectors[0][0] == 3 * 10000


def test_429_epuise_les_essais() -> None:
    fake = FakeClient(dim=4, failures={i: [FakeHTTPError(429)] for i in range(10)})
    with pytest.raises(EmbeddingError, match="essai"):
        embed(fake, ["a"], retry_occurrences=2, retry_time=1)
    assert len(fake.calls) == 3


def test_erreur_definitive_4xx_sans_retry() -> None:
    """4xx hors 429 : échec immédiat, sans consommer les essais (FR-008)."""
    fake = FakeClient(dim=4, failures={0: [FakeHTTPError(401)]})
    with pytest.raises(EmbeddingError, match="401"):
        embed(fake, ["a"], retry_occurrences=3, retry_time=1)
    assert len(fake.calls) == 1


def test_5xx_transitoire_puis_succes() -> None:
    fake = FakeClient(
        dim=4,
        failures={0: [FakeHTTPError(503)], 1: [FakeHTTPError(502)]},
    )
    vectors, sleep = embed(fake, ["a"], retry_time=2)
    assert sleep.delays == [2.0, 4.0]
    assert vectors[0][0] == 2 * 10000


def test_retry_occurences_zero() -> None:
    """0 retry : échec immédiat dès la première erreur transitoire."""
    fake = FakeClient(dim=4, failures={0: [FakeHTTPError(429)]})
    sleep = RecordingSleep()
    with pytest.raises(EmbeddingError):
        embed_texts(
            fake,
            "mistral-embed",
            ["a"],
            expected_dimension=4,
            batch_size=25,
            retry_occurrences=0,
            retry_time=3,
            sleep=sleep,
        )
    assert sleep.delays == []
    assert len(fake.calls) == 1


def test_erreur_non_transitoire_dans_un_lot_ulterieur() -> None:
    """Un lot sain ne masque pas l'échec définitif du lot suivant."""
    fake = FakeClient(dim=4, failures={1: [FakeHTTPError(422)]})
    with pytest.raises(EmbeddingError, match="422"):
        embed(fake, ["a", "b"], batch_size=1)


# --- Batching (FR-007, R-04) ---


def test_batching_par_lots_de_25() -> None:
    """100 chunks, lot de 25 : 4 appels, ordre préservé par extend."""
    texts = [f"chunk {i}" for i in range(100)]
    fake = FakeClient(dim=4)
    vectors, _ = embed(fake, texts, batch_size=25)
    assert len(fake.calls) == 4
    assert all(len(inputs) == 25 for _, inputs in fake.calls)
    # Ordre strict ligne i <-> chunk i : les lots se suivent sans
    # permutation (l'encodage du fake est indice_appel * 10000 + i).
    attendus = []
    for appel in range(4):
        attendus.extend(float(appel * 10000 + i) for i in range(25))
    assert [v[0] for v in vectors] == attendus


def test_taille_batch_zero_requete_simple() -> None:
    """--taille-batch 0 : une requête par chunk, sans regroupement."""
    texts = ["a", "b", "c"]
    fake = FakeClient(dim=4)
    vectors, _ = embed(fake, texts, batch_size=0)
    assert len(fake.calls) == 3
    assert all(len(inputs) == 1 for _, inputs in fake.calls)
    assert [v[0] for v in vectors] == [0.0, 10000.0, 20000.0]


def test_dimension_incoherente_echec_explicite() -> None:
    fake = FakeClient(dim=8)
    with pytest.raises(EmbeddingError, match="dimension"):
        embed(fake, ["a"], expected_dimension=4)


def test_skip_batches_ne_rappelle_pas_l_api() -> None:
    """Reprise : les lots déjà réussis (skip_batches) ne sont pas renvoyés."""
    texts = [f"c{i}" for i in range(20)]
    fake = FakeClient(dim=4)
    vectors, _ = embed(fake, texts, batch_size=5, skip_batches=2)
    # Seuls les lots 3 et 4 sont envoyés (indices d'appel 0 et 1).
    assert len(fake.calls) == 2
    assert all(len(inputs) == 5 for _, inputs in fake.calls)
    attendus = [float(i) for i in range(5)] + [10000.0 + i for i in range(5)]
    assert [v[0] for v in vectors] == attendus


def test_on_batch_done_recoit_l_accumulation() -> None:
    texts = [f"c{i}" for i in range(6)]
    fake = FakeClient(dim=4)
    snapshots: list[int] = []

    def _record(vectors_so_far: list[list[float]]) -> None:
        snapshots.append(len(vectors_so_far))

    embed_texts(
        fake,
        "mistral-embed",
        texts,
        expected_dimension=4,
        batch_size=3,
        retry_occurrences=0,
        retry_time=1,
        on_batch_done=_record,
        sleep=RecordingSleep(),
    )
    assert snapshots == [3, 6]
