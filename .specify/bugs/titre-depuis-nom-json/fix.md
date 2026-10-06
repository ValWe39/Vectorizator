# Bug Fix: Nom de sortie dérivé du nom de fichier du JSON

- **Slug**: titre-depuis-nom-json
- **Fixed**: 2026-10-06
- **Assessment**: ./assessment.md
- **Status**: applied

## Summary

Le nom des matrices de sortie reprend désormais les 18 premiers
caractères du nom de fichier du JSON d'entrée (stem, sans extension),
sanitisés, au lieu du champ `document.title` tronqué à 20. Code, tests
et documents de design ont été alignés sur la règle corrigée (FR-010).

## Changes

Code :

- `src/vectorizator/output.py` — modifié : troncature à 18
  (`NAME_LENGTH`) ; `sanitize_title` renommée `sanitize_name`.
- `src/vectorizator/cli.py` — modifié : `process_document` passe
  `Path(source).stem` à `save_matrix` ; title non utilisé.
- `src/vectorizator/checkpoint.py` — modifié : reporté sur
  `sanitize_name` (renommage).

Tests :

- `tests/unit/test_output.py` — troncature 18, stem de 18 exact, stem
  court, absence de `.json`, sanitisation.
- `tests/integration/test_single_document.py` — noms attendus
  `sample_index-0001.npy` / `-0002.npy`.

Documents :

- `specs/001-vectorisation-mistral-embed/spec.md` — FR-010, US1 (corps
  et scénario 3), 2 cas limites, entité Matrice, SC-007, assumption.
- `specs/001-vectorisation-mistral-embed/data-model.md` — §1
  `document.title`, §5 `nom`.
- `specs/001-vectorisation-mistral-embed/contracts/cli-contract.md`
  — section Sorties.
- `specs/001-vectorisation-mistral-embed/quickstart.md` — scénario 1
  (nom attendu `016472351681860015-0001.npy`).
- `specs/001-vectorisation-mistral-embed/research.md` — R-08 (décision
  corrigée, note historique).
- `README.md` — section Sorties.

## Diff Highlights (optional)

```python
# src/vectorizator/output.py — avant
def build_output_name(title: str, occurrence: str) -> str:
    return f"{sanitize_title(title)[:20]}-{occurrence}.npy"

# après
NAME_LENGTH = 18

def build_output_name(source_stem: str, occurrence: str) -> str:
    return f"{sanitize_name(source_stem)[:NAME_LENGTH]}-{occurrence}.npy"

# src/vectorizator/cli.py — après
path = save_matrix(output_dir, Path(source).stem, occurrence, vectors)
```

## Tests Added or Updated

- `tests/unit/test_output.py::test_troncature_a_18_caracteres_du_stem` —
  un stem de 26 caractères est tronqué à 18, pas un de plus.
- `tests/unit/test_output.py::test_stem_de_18_caracteres_pris_en_entier` —
  les exemples réels (18 chiffres) sont repris tels quels.
- `tests/unit/test_output.py::test_extension_json_absente_du_nom` —
  l'extension `.json` n'apparaît jamais dans le nom de sortie.
- `tests/unit/test_output.py::test_sanitisation_des_caracteres_interdits`
  et `test_sanitisation_puis_troncature_a_18` — sanitisation conservée.
- `tests/integration/test_single_document.py` (2 tests) — noms attendus
  depuis le stem du fichier (`sample_index-0001.npy`).

## Local Verification

- Commands run: `python -m pytest` → 104 passed (aucun échec).
- `python -m ruff check src tests` → All checks passed ;
  `python -m ruff format --check` → 27 files already formatted.
- `pre-commit run markdownlint-cli2 --files <6 docs modifiés>` → Passed.
- `check_constitution.py --diff HEAD` → OK (toutes les règles
  respectées).
- Manual checks : lecture croisée des 6 documents patchés — plus aucune
  occurrence de « 20 premiers caractères du titre » dans les
  spécifications actives.

## Deviations from Assessment

Aucune. Le renommage `sanitize_title` → `sanitize_name` (utilisé aussi
par `checkpoint.py`) est resté dans le périmètre « minimal et clair » ;
`tasks.md` (journal historique des tâches accomplies) n'a pas été
réécrit — sa description de T010 est historique.

## Follow-ups

- Re-valider le scénario 1 du quickstart en réel
  (`vector Examples/016472351681860015.json`) : sortie attendue
  `output/016472351681860015-0002.npy` (le compteur local est à 0001).
  À exécuter via `/speckit-bug-test slug=titre-depuis-nom-json` (appel
  API réel, ~247 chunks).
- L'ancienne sortie `output/Introduction aux Emb-0001.npy` (artefact
  local gitignoré) peut être supprimée à la main si souhaité.
- Committer l'ensemble : `/commit-push-ameliore 002-Noyau 5 phrases`.
