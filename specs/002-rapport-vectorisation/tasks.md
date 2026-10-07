---

description: "Task list template for feature implementation"

---

# Tasks: Rapport de traçabilité optionnel (`--rapport`)

**Input**: Design documents from `/specs/002-rapport-vectorisation/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md,
contracts/cli-contract.md, quickstart.md

**Tests**: inclus — exigés par spec.md (SC-002 : suite de tests
existante) et quickstart.md (scénario 6 : `pytest` doit passer sans
appel réseau).

**Organization**: tâches groupées par user story (US1 à US3, priorités
P1 à P3 de spec.md) pour implémentation et test indépendants.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: parallélisable (fichiers différents, aucune dépendance)
- **[Story]**: user story de rattachement (US1, US2, US3)
- Chemins exacts dans chaque description

## Path Conventions

- **Single project**: `src/`, `tests/` à la racine du dépôt
- Package `vectorizator`, layout `src/` (plan.md, Project Structure)

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: s'assurer d'un point de départ propre avant toute
modification du socle existant (feature 001)

- [ ] T001 Lancer la baseline de tests avant tout changement :
  `pytest` depuis la racine du dépôt — toutes les suites (unit +
  integration) doivent être vertes ; toute failure existante doit
  être résolue avant de commencer (fichiers : tests/)

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: option CLI partagée par toutes les user stories

**CRITICAL**: aucune user story ne peut commencer avant la fin de
cette phase

- [ ] T002 Ajouter l'option `--rapport` au parseur dans
  src/vectorizator/cli.py, fonction `build_parser` : flag booléen
  (`action="store_true"`, défaut `False`), aide documentant le rapport
  JSON par matrice réussie ; aucune borne à valider, aucune valeur
  (research.md R-06, contracts/cli-contract.md §Options)

## Phase 3: User Story 1 — Rapport de traçabilité par matrice (P1) — MVP

**Goal**: avec `--rapport`, chaque matrice réussie est accompagnée d'un
sidecar JSON de même nom, à cinq champs exacts

**Independent Test**: quickstart.md scénario 1 — `vector
Examples/016472351681860015.json --rapport` produit `.npy` + `.json` de
même nom ; les cinq clés correspondent à l'exécution ; aucun chemin
absolu ni clé

### Tests for User Story 1 (à écrire AVANT l'implémentation, doivent échouer)

- [ ] T003 [P] [US1] Tests unitaires de `save_report` dans
  tests/unit/test_output.py : nommage `<stem matrice>.json` dérivé de
  la même construction que la matrice ; cinq clés `entrée`, `sortie`,
  `embed`, `dimension`, `nature` avec valeurs exactes (nom de fichier
  seul, nom de matrice avec `.npy`, identifiant du modèle, entier du
  preset, nom du dtype de la matrice) ; UTF-8, indentation 2,
  retour à la ligne final ; jamais de chemin absolu ni de clé API
  (data-model.md §1, FR-004 à FR-006, FR-009)
- [ ] T004 [P] [US1] Test d'intégration dans tests/integration/
  (client SDK simulé, aucun réseau) : `vector <json> --rapport` →
  exit 0, une matrice + un rapport de même nom dans le dossier de
  sortie ; numéro d'occurrence identique entre les deux

### Implementation for User Story 1

- [ ] T005 [US1] Implémenter `save_report` dans
  src/vectorizator/output.py (dépend de T003) : nom dérivé de
  `build_output_name` avec extension `.json` (jamais recalculé
  indépendamment — research.md R-02) ; dictionnaire des cinq champs
  avec `entrée` = nom du fichier source seul (`source.name`),
  `sortie` = nom du fichier matrice, `embed` = valeur de
  `--choix-techno`, `dimension` = entier du preset (config.MODELS),
  `nature` = `matrix.dtype.name` de la matrice écrite (research.md
  R-03) ; écriture UTF-8, `json.dumps` indent 2, retour à la ligne
  final (research.md R-01)
- [ ] T006 [US1] Brancher le rapport dans src/vectorizator/cli.py :
  quand `args.rapport` est actif, appeler `save_report` immédiatement
  après `save_matrix` et avant `checkpoint.remove` (FR-007, research.md
  R-04) ; une `OSError` à l'écriture compte le document en échec avec
  message explicite, matrice conservée, checkpoint conservé, lot
  continué, exit 2 (FR-011, research.md R-05)
- [ ] T007 [US1] Valider US1 : `pytest` vert (T003, T004) et
  quickstart.md scénario 1 exécuté avec succès

**Checkpoint**: US1 fonctionnelle et testable indépendamment — MVP
atteignable ici

## Phase 4: User Story 2 — Comportement par défaut inchangé (P2)

**Goal**: sans `--rapport`, aucune modification observable : sorties,
console, codes de sortie identiques

**Independent Test**: quickstart.md scénario 2 — sans `--rapport`,
exactement un `.npy`, aucun `.json` de rapport, exit 0

### Tests for User Story 2

- [ ] T008 [P] [US2] Tests de non-régression dans
  tests/unit/test_cli.py : défaut du parseur `False` sans
  `--rapport` ; une exécution sans `--rapport` ne produit aucun
  fichier `.json` de rapport (SC-003) ; messages console et codes de
  sortie identiques au comportement sans la feature (SC-002)

### Implementation for User Story 2

- [ ] T009 [US2] Valider US2 : `pytest` complet vert et quickstart.md
  scénario 2 exécuté — aucune différence observable sans l'option

**Checkpoint**: US1 et US2 indépendamment vérifiées

## Phase 5: User Story 3 — Lot multi-documents avec échecs partiels (P3)

**Goal**: échec d'un document ou échec d'écriture d'un rapport :
matrice/rapport uniquement pour les réussites, lot continué, codes de
sortie corrects

**Independent Test**: quickstart.md scénario 4 — dossier contenant un
JSON valide et un JSON invalide → une paire `.npy`/`.json` pour le
valide, rien pour l'invalide, exit 2

### Tests for User Story 3

- [ ] T010 [US3] Test unitaire de l'échec d'écriture du rapport
  (FR-011) dans tests/unit/test_cli.py : écriture du rapport rendue
  impossible (permissions/disque simulés) → document compté en échec
  avec message explicite, matrice conservée, exit 2 (research.md R-05)
- [ ] T011 [P] [US3] Test d'intégration multi-input à échec partiel
  dans tests/integration/ (client SDK simulé) : lot d'un JSON valide
  et d'un JSON invalide avec `--rapport` → 1 paire matrice/rapport,
  aucune sortie pour l'invalide, exit 2 ; les numéros d'occurrence des
  rapports correspondent à leurs matrices (quickstart.md scénario 4)

### Implementation for User Story 3

- [ ] T012 [US3] Valider US3 : `pytest` vert et quickstart.md
  scénarios 4 et 5 exécutés (échec partiel ; re-vectorisation sans
  écrasement, numéros consécutifs)

**Checkpoint**: les trois user stories indépendamment fonctionnelles

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: validation transversale avant clôture

- [ ] T013 Exécuter quickstart.md en entier (scénarios 1 à 6) et les
  hooks pre-commit sur le code final (ruff, markdownlint,
  check-constitution) ; vérifier qu'aucun rapport de test ne pollue
  `output/` du dépôt

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: aucune dépendance — commencer immédiatement
- **Foundational (Phase 2)**: dépend de Phase 1 — BLOQUE toutes les
  user stories
- **User Stories (Phases 3 à 5)**: dépendent de Phase 2 ;
  US2 et US3 dépendent de l'implémentation de US1 (elles vérifient
  son comportement) ; US2 et US3 sont parallélisables entre elles
- **Polish (Phase 6)**: dépend de toutes les user stories

### User Story Dependencies

- **US1 (P1)**: commence après Phase 2 — aucune dépendance à une
  autre story
- **US2 (P2)**: après US1 (T005, T006) — teste le défaut de ce que US1
  implémente
- **US3 (P3)**: après US1 (T006 implémente FR-011 que US3 éprouve) ;
  parallélisable avec US2

### Within Each User Story

- Tests écrits AVANT l'implémentation, en échec d'abord
- `output.py` avant `cli.py` (fonction avant branchement)
- Validation de story (quickstart) avant de passer à la suivante

### Parallel Opportunities

- T003 et T004 (fichiers différents : tests/unit/test_output.py et
  tests/integration/)
- T008/T009 (US2) en parallèle de T010/T011 (US3), hors T010 qui
  partage tests/unit/test_cli.py avec T008 — séquencer T008 puis T010
  dans ce fichier
- T011 parallélisable avec T008/T010 (fichier d'intégration distinct)

## Parallel Example: User Story 1

```bash
# Écrire les tests de US1 en parallèle (fichiers différents) :
Task: "T003 Tests unitaires de save_report dans tests/unit/test_output.py"
Task: "T004 Test d'intégration --rapport dans tests/integration/"

# Puis implémentation séquentielle :
Task: "T005 save_report dans src/vectorizator/output.py"
Task: "T006 Branchement dans src/vectorizator/cli.py"
Task: "T007 Validation US1 (pytest + quickstart scénario 1)"
```

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1 : baseline `pytest` verte
2. Phase 2 : flag `--rapport` dans le parseur
3. Phase 3 : US1 complète (tests → save_report → branchement)
4. **STOP et VALIDER** : scénario 1 du quickstart — le rapport nominal
   fonctionne seul, sans régression

### Incremental Delivery

1. Setup + Foundational → socle prêt
2. US1 → validation indépendante → MVP (rapport nominal)
3. US2 → validation indépendante → défaut garanti inchangé
4. US3 → validation indépendante → échecs partiels maîtrisés
5. Polish → quickstart complet + hooks

## Notes

- [P] = fichiers différents, aucune dépendance
- Les contraintes de data-model.md §1 sont citées verbatim dans les
  tâches concernées (T003, T005) pour ne rien laisser à la discrétion
  de l'implémentation
- Aucune nouvelle dépendance : stdlib `json` uniquement (research.md
  R-07, Constitution III/IV)
- Committer après chaque tâche ou groupe logique ; valider chaque
  story à son checkpoint
