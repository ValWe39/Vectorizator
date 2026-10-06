"""Client SDK Mistral simulé : déterministe et traçable, sans réseau.

- Chaque appel est enregistré dans self.calls (modèle, liste des inputs).
- L'embedding du texte en position i de l'appel idx vaut
  [idx * 10000 + i, 0, 0, ...] : les tests vérifient l'ordre d'assemblage.
- failures : {index_d_appel: [exceptions à lever dans l'ordre]} pour
  simuler des erreurs transitoires ou définitives.
"""

from __future__ import annotations

from typing import Any


class FakeHTTPError(Exception):
    """Erreur HTTP simulée, classifiée par embedder via status_code."""

    def __init__(self, status_code: int) -> None:
        super().__init__(f"HTTP {status_code}")
        self.status_code = status_code


class _Data:
    def __init__(self, embedding: list[float]) -> None:
        self.embedding = embedding


class _Response:
    def __init__(self, embeddings: list[list[float]]) -> None:
        self.data = [_Data(e) for e in embeddings]


class FakeClient:
    """Fake de l'objet Mistral avec embeddings.create(model=..., inputs=...)."""

    def __init__(
        self,
        dim: int = 1024,
        failures: dict[int, list[Exception]] | None = None,
    ) -> None:
        self.dim = dim
        self.calls: list[tuple[str, list[str]]] = []
        self.failures = failures or {}

        class _Embeddings:
            def create(inner_self, model: str, inputs: list[str]) -> Any:  # noqa: N805
                return self._create(model, inputs)

        self.embeddings = _Embeddings()

    def _create(self, model: str, inputs: list[str]) -> _Response:
        idx = len(self.calls)
        self.calls.append((model, list(inputs)))
        errors = self.failures.get(idx, [])
        if errors:
            raise errors.pop(0)
        embeddings = []
        for i in range(len(inputs)):
            vector = [0.0] * self.dim
            vector[0] = float(idx * 10000 + i)
            embeddings.append(vector)
        return _Response(embeddings)
