"""Tests unitaires de vectorizator.output (T012, fix titre-depuis-nom-json)."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from vectorizator.output import build_output_name, sanitize_name, save_matrix


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
