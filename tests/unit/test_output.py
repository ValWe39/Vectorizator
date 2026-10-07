"""Tests unitaires de vectorizator.output (T012, fix titre-depuis-nom-json ;
T003, save_report du feature --rapport)."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from vectorizator.output import (
    build_output_name,
    sanitize_name,
    save_matrix,
    save_report,
)


def test_troncature_a_18_caracteres_du_stem() -> None:
    """18 premiers caractères du nom de fichier, pas un de plus (FR-010)."""
    stem = "01647235168186001512345678"  # 26 caractères
    name = build_output_name(stem, "0042")
    assert name == "016472351681860015-0042.npy"
    assert len(name.split("-")[0]) == 18


def test_stem_de_18_caracteres_pris_en_entier() -> None:
    """Les exemples réels ont un stem de 18 chiffres : repris tel quel."""
    name = build_output_name("016472351681860015", "0001")
    assert name == "016472351681860015-0001.npy"


def test_stem_court_pris_en_entier() -> None:
    name = build_output_name("sample_index", "0007")
    assert name == "sample_index-0007.npy"


def test_extension_json_absente_du_nom() -> None:
    """L'extension .json ne doit jamais apparaître dans le nom de sortie."""
    name = build_output_name("016472351681860015", "0001")
    assert ".json" not in name


def test_sanitisation_des_caracteres_interdits() -> None:
    brut = 'a/b\\c:d*e?f"g<h>i|j'
    assert sanitize_name(brut) == "a_b_c_d_e_f_g_h_i_j"
    assert sanitize_name("avec espaces") == "avec espaces"


def test_sanitisation_puis_troncature_a_18() -> None:
    """La troncature à 18 porte sur le stem sanitisé (R-08)."""
    stem = "a/b" * 15
    name = build_output_name(stem, "0001")
    assert name.startswith("a_b")
    assert len(name.split("-")[0]) == 18
    assert name == build_output_name(sanitize_name(stem), "0001")


def test_save_matrix_float32_et_dossier_cree(tmp_path: Path) -> None:
    out = tmp_path / "nested" / "output"
    vectors = [[1.5, 2.5], [3.5, 4.5]]
    path = save_matrix(out, "sample_index", "0003", vectors)
    assert path == out / "sample_index-0003.npy"
    assert path.exists()
    matrix = np.load(path)
    assert matrix.dtype == np.float32
    assert matrix.shape == (2, 2)
    assert matrix[0][0] == np.float32(1.5)


def test_save_matrix_preserve_l_ordre(tmp_path: Path) -> None:
    """Ligne i <-> vecteur i : l'ordre d'entrée est l'ordre des lignes."""
    vectors = [[10.0], [20.0], [30.0]]
    path = save_matrix(tmp_path, "doc", "0001", vectors)
    matrix = np.load(path)
    assert matrix[1][0] == np.float32(20.0)


# --- Feature --rapport : save_report (T003, data-model.md §1) ---


def _write_sample_matrix(tmp_path: Path) -> Path:
    return save_matrix(tmp_path, "sample_index", "0001", [[1.5, 2.5]])


def test_save_report_nom_identique_a_la_matrice(tmp_path: Path) -> None:
    """Le rapport porte le même nom que la matrice, en .json (FR-003)."""
    matrix_path = _write_sample_matrix(tmp_path)
    source = tmp_path / "sample_index.json"

    path = save_report(source, matrix_path, "mistral-embed", 1024)

    assert path == tmp_path / "sample_index-0001.json"
    assert path.exists()


def test_save_report_cinq_champs_exacts(tmp_path: Path) -> None:
    """Cinq clés, valeurs reflétant l'exécution réelle (FR-004 à FR-006)."""
    matrix_path = _write_sample_matrix(tmp_path)
    source = tmp_path / "sample_index.json"

    save_report(source, matrix_path, "mistral-embed-dim256-2510", 256)

    rapport = json.loads((tmp_path / "sample_index-0001.json").read_text("utf-8"))
    assert rapport == {
        "entrée": "sample_index.json",
        "sortie": "sample_index-0001.npy",
        "embed": "mistral-embed-dim256-2510",
        "dimension": 256,
        "nature": "float32",
    }


def test_save_report_utf8_indente_final_newline(tmp_path: Path) -> None:
    """UTF-8, indentation 2, retour à la ligne final (research.md R-01)."""
    matrix_path = _write_sample_matrix(tmp_path)
    content = save_report(
        tmp_path / "sample_index.json", matrix_path, "mistral-embed", 1024
    ).read_text(encoding="utf-8")

    assert content.endswith("\n")
    assert '\n  "entrée"' in content
    content.encode("utf-8")


def test_save_report_aucun_chemin_absolu_ni_cle(tmp_path: Path) -> None:
    """Jamais de chemin absolu ni de clé API dans le rapport (FR-009)."""
    matrix_path = _write_sample_matrix(tmp_path)

    path = save_report(tmp_path / "sample_index.json", matrix_path, "m", 1024)

    content = path.read_text(encoding="utf-8")
    assert str(tmp_path) not in content
    assert "MISTRAL_API_KEY" not in content
    assert "cle-de-test" not in content


def test_save_report_lu_depuis_la_matrice_ecrite(tmp_path: Path) -> None:
    """La nature est le dtype de la matrice écrite, pas une constante."""
    matrix_path = save_matrix(tmp_path, "doc", "0001", [[1.0]])
    assert np.load(matrix_path).dtype.name == "float32"
    save_report(tmp_path / "doc.json", matrix_path, "mistral-embed", 1024)
    rapport = json.loads((tmp_path / "doc-0001.json").read_text("utf-8"))
    assert rapport["nature"] == np.load(matrix_path).dtype.name
