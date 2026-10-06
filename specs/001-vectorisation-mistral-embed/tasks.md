---

description: "Task list template for feature implementation"
---

# Tasks: Vectorisation JSON via Mistral Embed

**Input**: Design documents from `/specs/001-vectorisation-mistral-embed/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md,
contracts/cli-contract.md, quickstart.md

**Tests**: inclus — exigés par plan.md (pytest) et quickstart.md
(scénario 8 : `pytest` doit passer sans appel réseau).

**Organization**: tâches groupées par user story (US1 à US4, priorités
P1 à P4 de spec.md) pour implémentation et test indépendants.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: parallélisable (fichiers différents, aucune dépendance)
- **[Story]**: user story de rattachement (US1, US2, US3, US4)
- Chemins exacts dans chaque description

## Path Conventions

- **Single project**: `src/`, `tests/` à la racine du dépôt
- Package `vectorizator`, layout `src/` (plan.md, Project Structure)

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: initialisation du projet Python et structure de base

- [x] T001 Créer pyproject.toml : deps mistralai, numpy,
  python-dotenv ; entry point `vector = vectorizator.cli:main` ;
  requires-python >= 3.11 ; config ruff (fichier : pyproject.toml)
- [x] T002 [P] Créer le squelette du package
  `src/vectorizator/__init__.py` (version, docstring package)
- [x] T003 [P] Créer .env.example avec uniquement le placeholder
  `MISTRAL_API_KEY=YOUR_API_KEY` (jamais de clé réelle — Constitution I)
- [x] T004 [P] Configurer pytest (section pyproject) et créer
  tests/unit/, tests/integration/ et tests/conftest.py avec un
  fixture de client SDK simulé (aucun réseau dans les tests)

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: infrastructure commune bloquant toutes les user stories

**CRITICAL**: aucune user story ne peut commencer avant la fin de
cette phase

- [x] T005 [P] Implémenter src/vectorizator/config.py : chargement
  .env via python-dotenv, lecture MISTRAL_API_KEY (échec rapide si
  absente/vide), presets {mistral-embed: 1024 (défaut),
  mistral-embed-dim256-2510: 256, mistral-embed-dim128-2510: 128}
  (cf. research.md R-01 à R-03, data-model.md §3)
- [x] T006 [P] Implémenter src/vectorizator/schema.py : validation du
  schéma 1.0 — schema_version == "1.0", document.title chaîne non
  vide, chunks liste non vide, chaque chunk : ref entier + text
  chaîne non vide ; autres champs lus sans interprétation ; erreurs
  explicites avec le chemin d'input (data-model.md §1-2)
- [x] T007 [P] Implémenter src/vectorizator/cli.py : argparse,
  `vector INPUT...`, options --choix-techno, --taille-batch (0-100),
  --retry-occurences (0-10), --retry-time (1-10), --output-folder ;
  validation des bornes fail-fast ; codes de sortie 0/1/2
  (contracts/cli-contract.md)
- [x] T008 [P] Écrire tests/unit/test_config.py (clé absente ->
  échec, presets), tests/unit/test_schema.py (JSON valides/invalides
  des Examples/), tests/unit/test_cli.py (bornes, codes de sortie)

## Phase 3: User Story 1 - Vectoriser un JSON unique (Priority: P1) — MVP

**Goal**: un JSON d'index -> une matrice NumPy ordonnée, nommée
`<titre 20 car.>-<NNNN>.npy`, dans le dossier de sortie

**Independent Test**: exécuter `vector Examples/016472351681860015.json`
-> matrice (n_chunks x 1024) dans output/, lignes dans l'ordre des
chunks (quickstart.md scénario 1)

- [x] T009 [P] [US1] Implémenter src/vectorizator/counter.py :
  compteur counter.txt à la racine (uniquement le dernier numéro, 4
  chiffres) ; absent -> 0001 ; illisible/corrompu -> échec rapide sans
  sortie ; cycle 0001..9999 -> 0000 -> 0001 ; persisté après chaque
  document produit, avant l'écriture de la matrice (data-model.md §6)
- [x] T010 [P] [US1] Implémenter src/vectorizator/output.py : nom
  `<20 premiers caractères du titre sanitisé>-<NNNN>.npy` ;
  sanitisation de `/ \ : * ? " < > |` et caractères de contrôle en
  `_` (espaces conservés) ; création du dossier si absent ;
  numpy.save en float32 (research.md R-08, data-model.md §5)
- [x] T011 [P] [US1] Écrire tests/unit/test_counter.py : premier
  usage 0001, incrément, cycle 9999 -> 0000 -> 0001, corrompu ->
  échec, jamais de réutilisation
- [x] T012 [P] [US1] Écrire tests/unit/test_output.py : troncature
  à 20, sanitisation, titre court pris en entier, dossier créé,
  dtype float32
- [x] T013 [US1] Implémenter src/vectorizator/embedder.py : appel
  synchrone client.embeddings.create(model, inputs), assemblage par
  extend (ordre ligne i <-> chunk i), contrôle dimension renvoyée ==
  dimension du preset (research.md R-01, R-03)
- [x] T014 [US1] Implémenter le pipeline mono-document dans
  src/vectorizator/cli.py : lire JSON -> valider -> embedder ->
  numéro -> sauvegarder ; ordre des lignes strictement celui des
  chunks
- [x] T015 [US1] Écrire tests/integration/test_single_document.py :
  pipeline complet avec client simulé sur un JSON des Examples/
  (shape, ordre, nom de fichier, compteur incrémenté)

## Phase 4: User Story 2 - Multi-input transparent (Priority: P2)

**Goal**: un fichier, plusieurs fichiers ou un dossier détectés
automatiquement ; N inputs = N sorties, indépendantes

**Independent Test**: exécuter `vector Examples/` -> 4 matrices,
numéros consécutifs, fichiers non-JSON ignorés (quickstart.md
scénario 2)

- [x] T016 [P] [US2] Implémenter src/vectorizator/inputs.py :
  détection automatique fichier / fichiers / dossier, filtrage des
  *.json uniquement, tri alphabétique stable, dossier sans JSON ->
  message explicite sans consommer de numéro (data-model.md §1,
  spec.md FR-001/FR-002)
- [x] T017 [P] [US2] Écrire tests/unit/test_inputs.py : dossier mixte
  (JSON + non-JSON), plusieurs chemins, dossier vide, tri
  alphabétique
- [x] T018 [US2] Implémenter la boucle multi-documents dans
  src/vectorizator/cli.py : chaque JSON traité indépendamment,
  l'échec d'un document n'interrompt pas les suivants, exit 2 si au
  moins un échec, exit 1 sur erreur de configuration (contracts/
  cli-contract.md, spec.md FR-003)
- [x] T019 [US2] Écrire tests/integration/test_multi_input.py :
  dossier Examples/ -> 4 matrices, 4 numéros consécutifs sans
  doublon ; échec d'un document n'empêche pas les suivants

## Phase 5: User Story 3 - Pannes réseau : batch, retry, reprise (Priority: P3)

**Goal**: lots de chunks, retry exponentiel sur transitoires
uniquement, reprise au lot échoué sans recalcul

**Independent Test**: échec simulé au 3e lot d'un document de 100
chunks -> relance -> seuls les lots restants sont renvoyés ; checkpoint
supprimé après succès (quickstart.md scénario 5)

- [x] T020 [P] [US3] Écrire tests/unit/test_retry.py : délais doublés
  (t, 2t, 4t), nombre d'essais, transitoire (429/5xx/timeout) retenté,
  définitif (4xx hors 429) échoue immédiatement
- [x] T021 [US3] Implémenter le retry dans src/vectorizator/
  embedder.py : retry exponentiel uniquement sur erreurs
  transitoires (timeout, réseau, 429, 5xx) ; échec immédiat du
  document pour 4xx hors 429, sans consommer les essais
  (research.md R-05, spec.md FR-008)
- [x] T022 [US3] Implémenter le batching dans src/vectorizator/
  embedder.py : lots de N chunks (N de --taille-batch, plafond 100),
  N = 0 -> requête simple par chunk sans regroupement ; ordre
  préservé par extend (research.md R-04, spec.md FR-007)
- [x] T023 [P] [US3] Implémenter src/vectorizator/checkpoint.py :
  `<output>/.checkpoints/<nom d'input sanitisé>.json` contenant
  {model, batch_size, vectors} ; enrichi à chaque lot réussi ;
  supprimé après écriture de la matrice ; invalidé avec avertissement
  si model change (research.md R-06, data-model.md §7)
- [x] T024 [P] [US3] Écrire tests/unit/test_checkpoint.py : création,
  enrichissement, suppression après succès, invalidation si modèle
  différent
- [x] T025 [US3] Implémenter la reprise dans le pipeline
  src/vectorizator/cli.py : au relancement, charger le checkpoint, ne
  renvoyer à l'API que les lots non réussis, compléter la matrice,
  supprimer le checkpoint (spec.md FR-009)
- [x] T026 [US3] Écrire tests/integration/test_resume.py : échec
  simulé au 3e lot (client simulé) -> relance -> seuls les lots 3 et
  4 renvoyés ; matrice complète et ordonnée ; checkpoint supprimé

## Phase 6: User Story 4 - Configuration via options CLI (Priority: P4)

**Goal**: chaque option produit l'effet documenté, avec les défauts
du contrat

**Independent Test**: `--choix-techno mistral-embed-dim256-2510` ->
256 colonnes ; `--taille-batch 0` -> requêtes simples (quickstart.md
scénarios 3-4)

- [x] T027 [P] [US4] Écrire tests/unit/test_options.py : défauts
  (mistral-embed, 25, 3, 3 s, output) et refus des valeurs hors
  bornes
- [x] T028 [US4] Câbler --choix-techno dans src/vectorizator/cli.py :
  trois valeurs exactes, défaut mistral-embed, dimension de la
  matrice = dimension du preset (spec.md FR-006)
- [x] T029 [US4] Câbler --taille-batch dans src/vectorizator/cli.py :
  défaut 25, 0-100, 0 = pas de batch (spec.md FR-007)
- [x] T030 [US4] Câbler --retry-occurences et --retry-time dans
  src/vectorizator/cli.py : défauts 3 et 3 s, premier délai puis
  doublement à chaque essai (spec.md FR-008)
- [x] T031 [US4] Câbler --output-folder dans src/vectorizator/
  cli.py : défaut `output` à la racine du projet, créé si absent
  (spec.md FR-014)
- [x] T032 [US4] Écrire tests/integration/test_options.py : 256 et
  128 colonnes via --choix-techno, --taille-batch 0 sans batch,
  --output-folder alternatif créé

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: finitions transversales aux quatre stories

- [x] T033 [P] Documenter l'usage dans README.md : commande `vector`,
  options avec bornes, .env.example, exemple de sortie — sans clé
  réelle ni chemin personnel
- [x] T034 Vérifier la conformité Constitution : la clé n'apparaît
  dans aucun fichier écrit/log, trafic sortant limité à l'endpoint
  embeddings, .gitignore couvre .env et output/ (Constitution I, II,
  Network Surface)
- [x] T035 Exécuter la validation complète de quickstart.md
  (scénarios 1 à 8) et passer pre-commit sur l'ensemble du dépôt

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: aucune dépendance, démarrage immédiat
- **Foundational (Phase 2)**: dépend de Phase 1 — BLOQUE toutes les
  user stories
- **User Stories (Phases 3-6)**: dépendent de Phase 2 ; ensuite
  exécution en parallèle possible ou séquentielle par priorité
  (P1 -> P2 -> P3 -> P4)
- **Polish (Phase 7)**: dépend des stories livrées retenues

### User Story Dependencies

- **US1 (P1)**: démarre après Phase 2 — aucune dépendance envers une
  autre story (MVP autonome : JSON unique -> matrice)
- **US2 (P2)**: démarre après Phase 2 — réutilise le pipeline de US1
  mais reste testable indépendamment
- **US3 (P3)**: démarre après Phase 2 — s'appuie sur embedder.py
  (US1) pour le batching et le retry ; testable indépendamment
- **US4 (P4)**: démarre après Phase 2 — câble les options sur les
  mécanismes de US1/US3 ; testable indépendamment

### Within Each User Story

- Tests écrits en premier et échouant avant implémentation
- Modules (counter, output, inputs, checkpoint) avant pipeline
- Pipeline avant tests d'intégration
- Story complète avant de passer à la priorité suivante

### Parallel Opportunities

- Toutes les tâches [P] de Phase 1 et 2 en parallèle
- T009/T010/T011/T012 (US1) en parallèle ; T016/T017 (US2) en
  parallèle ; T020/T023/T024 (US3) en parallèle ; T027 (US4) en
  parallèle des câblages
- Une fois la Phase 2 terminée, les stories peuvent être traitées en
  parallèle par des personnes différentes

---

## Parallel Example: User Story 1

```bash
# Modules et tests US1 en parallèle (fichiers distincts):
Task: "T009 Compteur dans src/vectorizator/counter.py"
Task: "T010 Nommage/sauvegarde dans src/vectorizator/output.py"
Task: "T011 tests/unit/test_counter.py"
Task: "T012 tests/unit/test_output.py"
# Puis séquentiel (même fichier pipeline):
Task: "T013 embedder.py" -> "T014 pipeline cli.py" -> "T015 intégration"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Compléter Phase 1 : Setup
2. Compléter Phase 2 : Foundational (CRITICAL — bloque tout)
3. Compléter Phase 3 : User Story 1
4. **STOP et VALIDER** : quickstart.md scénario 1 (JSON unique ->
   matrice ordonnée et nommée)
5. Démo/déploiable si suffisant

### Incremental Delivery

1. Setup + Foundational -> fondation prête
2. US1 -> test indépendant -> MVP (JSON unique)
3. US2 -> test indépendant -> multi-input/dossier
4. US3 -> test indépendant -> robustesse réseau complète
5. US4 -> test indépendant -> configurabilité totale
6. Polish -> validation quickstart complète, conformité, doc

### Parallel Team Strategy

1. L'équipe complète Setup + Foundational ensemble
2. Après Phase 2 : développeur A -> US1, B -> US2, C -> US3,
   D -> US4
3. Chaque story livrée et testée indépendamment

---

## Notes

- [P] = fichiers différents, aucune dépendance
- [Story] = traçabilité vers spec.md ; setups/fondation/polish sans
  label de story
- Chaque story est complétable et testable indépendamment
- Vérifier que les tests échouent avant d'implémenter
- Committer après chaque tâche ou groupe logique
- S'arrêter à chaque checkpoint pour valider la story
- À éviter : tâches vagues, conflits sur un même fichier,
  dépendances inter-stories qui brisent l'indépendance
- En cas de conflit de documentation, la doc Mistral prime sur le
  cours Corsen AI (règle de précédence, research.md)
