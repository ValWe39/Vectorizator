"""Tests unitaires de vectorizator.inputs (T017)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from vectorizator.inputs import InputsError, collect_inputs


def write_index(path: Path, title: str = "T") -> None:
    path.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "document": {"title": title},
                "chunks": [{"ref": 1, "text": "texte"}],
            }
        ),
        encoding="utf-8",
    )


def test_fichier_unique(tmp_path: Path) -> None:
    write_index(tmp_path / "a.json")
    result = collect_inputs([str(tmp_path / "a.json")])
    assert result == [tmp_path / "a.json"]


def test_dossier_mixte_ignorer_non_json(tmp_path: Path) -> None:
    """Dossier : seuls les .json sont retenus (FR-002)."""
    write_index(tmp_path / "b.json")
    write_index(tmp_path / "a.json")
    (tmp_path / "notes.txt").write_text("pas un json", encoding="utf-8")
    (tmp_path / "data.csv").write_text("x,y", encoding="utf-8")
    result = collect_inputs([str(tmp_path)])
    assert result == [tmp_path / "a.json", tmp_path / "b.json"]


def test_plusieurs_chemins_melanges(tmp_path: Path) -> None:
    dossier = tmp_path / "d"
    dossier.mkdir()
    write_index(dossier / "z.json")
    write_index(tmp_path / "solo.json")
    result = collect_inputs([str(dossier), str(tmp_path / "solo.json")])
    assert result == [dossier / "z.json", tmp_path / "solo.json"]


def test_dossier_sans_json(tmp_path: Path) -> None:
    (tmp_path / "lisezmoi.txt").write_text("rien", encoding="utf-8")
    assert collect_inputs([str(tmp_path)]) == []


def test_tri_alphabetique_stable(tmp_path: Path) -> None:
    """Ordre déterministe : tri alphabétique (assumption de la spec)."""
    for name in ["c.json", "a.json", "b.json"]:
        write_index(tmp_path / name)
    result = collect_inputs([str(tmp_path)])
    assert [p.name for p in result] == ["a.json", "b.json", "c.json"]


def test_chemin_inexistant() -> None:
    with pytest.raises(InputsError, match="introuvable"):
        collect_inputs(["c:/nul/part/ici.json"])
