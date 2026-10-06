# Bug Assessment: Nom de sortie dérivé du nom de fichier du JSON

- **Slug**: titre-depuis-nom-json
- **Created**: 2026-10-06
- **Source**: pasted text (signalement utilisateur)
- **Verdict**: valid
- **Severity**: medium

## Report (verbatim or summarized)

Signalement : « Il y a eu une incompréhension concernant ma demande
initiale sur le titre du document de sortie : les 18 premiers caractères
doivent être ceux du titre du Json : "XXXXXXXXXXXXXXXXXX.json". Pas ceux
de l'élément "titre" dans le Json ! »

Clarifications obtenues (2026-10-06) :

- Troncature à **18 caractères** (et non 20 comme écrit par erreur dans
  la spec initiale).
- Le nom de sortie reprend le **nom de fichier du JSON sans son
  extension** (« stem ») : l'extension `.json` n'apparaît jamais dans le
  nom de sortie.

## Symptom

Les matrices de sortie sont nommées d'après le champ `document.title`
du JSON d'entrée (ex. `Introduction aux Emb-0001.npy`), alors qu'elles
doivent être nommées d'après les 18 premiers caractères du nom de
fichier du JSON, sans extension (ex. `016472351681860015-0001.npy` pour
`Examples/016472351681860015.json`).

## Reproduction

1. Exécuter `vector Examples/016472351681860015.json`.
2. Constater la sortie `output/Introduction aux Emb-0001.npy`
   (constaté en réel le 2026-10-06, commit non encore poussé).
3. Attendu : `output/016472351681860015-0001.npy`.

## Suspected Code Paths

- `src/vectorizator/output.py:build_output_name()` — reprend
  `sanitize_title(title)[:20]` : mauvaise source (title) et mauvaise
  longueur (20).
- `src/vectorizator/cli.py:process_document()` — passe `title` (issu de
  `validate_index`) à `save_matrix` pour le nommage.
- `src/vectorizator/schema.py:validate_index()` — retourne le title :
  source de la dérive, mais la validation du champ reste pertinente.
- `specs/001-vectorisation-mistral-embed/spec.md` FR-010 — exigence
  erronée à l'origine (« titre du .md d'entrée » interprété comme
  `document.title`, et « 20 caractères » au lieu de 18).

## Root Cause Hypothesis

Erreur d'interprétation des exigences lors de `/speckit-specify` : la
formulation « les 20 premiers caractères du titre du .md d'entrée » a
été comprise comme le champ `document.title` du JSON d'index, avec une
longueur de 20, alors que l'intention était les 18 premiers caractères
du nom de fichier du JSON (sans extension). L'implémentation est
conforme à la spec erronée ; le bug est donc un défaut de spécification
propagé jusqu'au code, aux tests et à la documentation. Confiance :
haute (confirmé par l'utilisateur et par lecture du code).

## Proposed Remediation

**Preferred** : corriger la chaîne complète — spec, artefacts de design,
code et tests. Le nom de sortie devient
`<stem du nom de fichier du JSON, sanitisé, tronqué à 18>-<NNNN>.npy` :

1. Spec/design : FR-010, data-model §5, contracts/cli-contract.md,
   quickstart.md (scénarios 1 et 6), research.md R-08, README : « 18
   premiers caractères du nom de fichier du JSON d'entrée, sans
   extension » ; le champ `document.title` reste validé à l'entrée mais
   ne sert plus au nommage.
2. Code : `output.build_output_name(source_stem, occurrence)` tronque à
   18 après sanitisation ; `cli.process_document` passe
   `Path(source).stem` au lieu de `title`.
3. La sanitisation reste appliquée (un nom de fichier peut contenir
   des caractères interdits) ; le compteur, l'ordre et le reste du
   pipeline sont inchangés.

**Alternatives** : conserver le title en suffixe du nom — rejeté
(non demandé, allonge les noms) ; tronquer à 20 — rejeté (l'utilisateur
a explicitement fixé 18).

**Files likely to change**:

- `src/vectorizator/output.py`
- `src/vectorizator/cli.py`
- `tests/unit/test_output.py`
- `tests/integration/test_single_document.py`
- `tests/integration/test_multi_input.py`
- `specs/001-vectorisation-mistral-embed/spec.md`
- `specs/001-vectorisation-mistral-embed/data-model.md`
- `specs/001-vectorisation-mistral-embed/contracts/cli-contract.md`
- `specs/001-vectorisation-mistral-embed/quickstart.md`
- `specs/001-vectorisation-mistral-embed/research.md`
- `README.md`

**Tests to add or update**:

- `test_output.py` : nommage depuis un stem de 18+ caractères (tronqué
  à 18), stem plus court (pris en entier), sanitisation du stem,
  absence de l'extension `.json` dans le nom produit.
- Tests d'intégration : sortie attendue `sample_index-0001.npy` pour
  `tests/data/sample_index.json`, et
  `016472351681860015-0001.npy` pour l'exemple réel.

## Risks & Considerations

- Deux fichiers JSON partageant les mêmes 18 premiers caractères de
  stem produisent le même préfixe, mais le numéro d'occurrence distinct
  garantit l'absence de collision (FR-011) — inchangé.
- Les sorties déjà produites avec l'ancien nommage (`output/`, dossier
  gitignoré) ne sont pas migrées : sans conséquence, régénérables.
- Le champ `document.title` reste requis par la validation du schéma :
  aucun assouplissement demandé.
- Attention à ne pas casser les tests existants qui dérivent le nom
  attendu du title (scénarios 1/6 du quickstart).

## Open Questions

Aucune — troncature à 18 et exclusion de l'extension confirmées par
l'utilisateur le 2026-10-06.
