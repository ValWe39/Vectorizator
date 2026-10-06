# Implementation Plan: Vectorisation JSON via Mistral Embed

**Branch**: `002-Noyau` | **Date**: 2026-10-06 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/001-vectorisation-mistral-embed/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command; its
definition describes the execution workflow.

## Summary

Outil CLI `vector` qui vectorise les chunks de JSON d'index (schéma 1.0)
en matrices NumPy via l'API Mistral Embeddings. Multi-input transparent
(un fichier, plusieurs fichiers, un dossier), batching (25 par défaut,
plafond 100), retry exponentiel sur erreurs transitoires uniquement,
reprise au lot échoué via checkpoints persistants, numérotation
d'occurrence persistée (cycle 0001..9999 puis 0000), sorties `.npy`
nommées `<20 premiers caractères du titre>-<NNNN>.npy` dans le dossier
de sortie, ordre des lignes strictement aligné sur l'ordre des chunks.

## Technical Context

**Language/Version**: Python 3.11+ (outillage existant du dépôt : Ruff,
pre-commit, scripts Python de conformité)

**Primary Dependencies**: `mistralai` (SDK officiel Mistral, MIT —
`client.embeddings.create(model, inputs)`), `numpy` (BSD — matrices
`.npy`), `python-dotenv` (BSD — chargement du `.env`)

**Storage**: fichiers locaux uniquement — sorties `.npy`, compteur
`counter.txt` à la racine du projet, checkpoints JSON sous
`<output>/.checkpoints/`

**Testing**: pytest — tests unitaires avec client SDK simulé (aucun
réseau), tests d'intégration du pipeline complet sur `Examples/`

**Target Platform**: CLI multiplateforme (Windows / Linux / macOS),
Python 3.11+, aucun service distant déployé

**Project Type**: cli

**Performance Goals**: 25 chunks par lot par défaut ; ordre des vecteurs
strictement aligné sur l'ordre des chunks (assemblage par `extend`) ;
dimensions 1024 / 256 / 128 selon le modèle

**Constraints**: réseau sortant limité à l'endpoint Mistral
`/v1/embeddings` ; aucun tracker ; secret uniquement via
`MISTRAL_API_KEY` (`.env` gitignoré) ; retry seulement sur erreurs
transitoires (timeout, réseau, 429, 5xx) ; plafond 100 chunks par lot

**Scale/Scope**: corpus de quelques centaines de documents, plusieurs
milliers de chunks ; matrices (n_chunks x 128/256/1024) en float32

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Gates (Constitution v1.4.0) :

- **I. Isolation des secrets** : PASS — clé lue uniquement depuis la
  variable d'environnement `MISTRAL_API_KEY` (`.env` déjà gitignoré),
  jamais logguée ni écrite ; placeholders dans les exemples.
- **II. Local-first** : PASS avec exception explicite — sorties, compteur
  et checkpoints strictement locaux ; les textes des chunks sont transmis
  à l'API Mistral d'embedding, demande explicite de l'utilisateur actée
  dans la spec (seul usage réseau autorisé).
- **III. Open-source & sans trackers** : PASS — `numpy` (BSD),
  `python-dotenv` (BSD), `mistralai` (MIT, SDK officiel) ; aucune
  dépendance de télémétrie ; licences permissives compatibles MIT.
- **IV. Simplicité (YAGNI)** : PASS — un seul point d'entrée CLI
  (`argparse`, stdlib), pas de plugins, pas de serveur, pas de GUI.
- **Network Surface** : PASS — appels sortants limités à l'URL de l'API
  Mistral embeddings, explicitement demandée par l'utilisateur.
- **Préférence outils souverains** : PASS — Mistral AI (européen) et
  dépendances à licences permissives.

Re-check post-Phase 1 : inchangé, tous les gates passent — aucune décision
de design (research.md, data-model.md, contracts/, quickstart.md)
n'introduit de cloud, de tracker, ni de secret persisté.

## Project Structure

### Documentation (this feature)

```text
specs/001-vectorisation-mistral-embed/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
│   └── cli-contract.md  # Schéma de commandes de l'outil
└── checklists/requirements.md
```

### Source Code (repository root)

```text
pyproject.toml           # packaging, entry point `vector`, deps, ruff
src/vectorizator/
├── __init__.py
├── cli.py               # argparse, `vector`, validation des bornes
├── config.py            # MISTRAL_API_KEY via .env/env, presets modèles
├── inputs.py            # détection 1 fichier / N fichiers / dossier
├── schema.py            # validation du schéma JSON 1.0
├── embedder.py          # presets, batching, retry exponentiel
├── checkpoint.py        # état de reprise par document (JSON)
├── counter.py           # compteur d'occurrence persistant (cycle)
└── output.py            # nommage, dossier de sortie, sauvegarde .npy

tests/
├── unit/                # counter, checkpoint, inputs, schema, output
└── integration/         # pipeline complet sur Examples/, client simulé
```

**Structure Decision**: projet unique (single project) en layout `src/` —
package `vectorizator`, entry point console `vector` pointant vers
`vectorizator.cli:main`. Tests séparés unit/integration ; les tests du
contrat CLI vivent dans `tests/unit/test_cli.py`.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

Aucune violation à justifier — table omise.
