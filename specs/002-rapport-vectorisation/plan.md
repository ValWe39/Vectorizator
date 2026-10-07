# Implementation Plan: Rapport de traçabilité optionnel (`--rapport`)

**Branch**: `003-rapport` | **Date**: 2026-10-07 | **Spec**:
[spec.md](spec.md)

**Input**: Feature specification from
`specs/002-rapport-vectorisation/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command; its
definition describes the execution workflow.

## Summary

Option `--rapport` du CLI `vector` (booléenne, désactivée par défaut) :
chaque matrice `.npy` écrite avec succès est accompagnée d'un rapport
JSON de même nom (extension `.json`) décrivant le document d'entrée, la
matrice produite, le modèle d'embedding, la dimension et la nature des
flottants. Approche technique : extension minimale de l'existant —
flag `argparse`, fonction d'écriture à côté de `save_matrix` dans
`output.py`, branchement dans `cli.py` après l'écriture de la matrice ;
aucune nouvelle dépendance (stdlib `json`), aucun appel réseau, aucune
modification du comportement par défaut.

## Technical Context

**Language/Version**: Python 3.11+ (existant)

**Primary Dependencies**: aucune nouvelle — stdlib `json` (écriture du
rapport) ; le socle existant reste `numpy`, `mistralai`, `python-dotenv`

**Storage**: fichier JSON sidecar par matrice, dans le dossier de
sortie (`output` par défaut), même nom que la matrice avec l'extension
`.json`

**Testing**: pytest — tests unitaires hors réseau (nommage du rapport,
contenu des cinq champs, défaut sans l'option, échec d'écriture) et
test d'intégration du pipeline avec client SDK simulé

**Target Platform**: CLI multiplateforme (Windows / Linux / macOS),
Python 3.11+ ; l'écriture du rapport est un simple fichier local

**Project Type**: cli (extension du CLI `vector` existant)

**Performance Goals**: négligeables — un fichier texte de quelques
dizaines d'octets par document réussi, écriture locale immédiate

**Constraints**: opt-in strict (`--rapport` désactivée par défaut,
sorties et codes de sortie inchangés sans l'option) ; aucun réseau
supplémentaire ; jamais de clé API ni de chemin absolu dans le rapport ;
rapport écrit seulement après l'écriture réussie de la matrice

**Scale/Scope**: 1 rapport par document réussi quand l'option est
active ; quelques centaines de documents au plus

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1
design.*

Gates (Constitution v1.4.0) :

- **I. Isolation des secrets** : PASS — le rapport ne contient que des
  noms de fichiers et des paramètres d'exécution ; la clé API n'y
  figure jamais ; aucun chemin absolu (FR-009).
- **II. Local-first** : PASS — le rapport est un fichier local dans le
  dossier de sortie ; aucune donnée ne quitte la machine ; aucun appel
  réseau (FR-010) ; testable hors ligne.
- **III. Open-source & sans trackers** : PASS — stdlib `json`
  uniquement ; aucune nouvelle dépendance.
- **IV. Simplicité (YAGNI)** : PASS — un flag `argparse`, une fonction
  d'écriture ; pas de schéma versionné, pas d'horodatage, pas de
  manifest global (rejeté en assessment).
- **Network Surface** : PASS — aucun nouveau trafic sortant ; la
  surface réseau reste limitée à l'endpoint Mistral `/v1/embeddings`.
- **Préférence outils souverains** : PASS — aucune dépendance ajoutée.

Re-check post-Phase 1 : inchangé, tous les gates passent — les décisions
de research.md et data-model.md n'introduisent ni service distant, ni
dépendance, ni secret persisté.

## Project Structure

### Documentation (this feature)

```text
specs/002-rapport-vectorisation/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
│   └── cli-contract.md  # Amendement du contrat CLI : option --rapport
└── checklists/requirements.md
```

### Source Code (repository root)

```text
pyproject.toml           # inchangé (aucune nouvelle dépendance)
src/vectorizator/
├── cli.py               # option --rapport, branchement du rapport
└── output.py            # save_report : nommage et écriture du sidecar

tests/
├── unit/
│   ├── test_output.py   # nommage + contenu du rapport, défaut sans option
│   └── test_cli.py      # parse --rapport, codes de sortie inchangés
└── integration/         # pipeline complet avec rapport, client simulé
```

**Structure Decision**: projet unique existant (layout `src/`) — la
feature étend `output.py` (fonction `save_report` à côté de
`save_matrix`, même module pour cohérence du nommage) et `cli.py`
(flag + branchement après l'écriture de la matrice, avant la suppression
du checkpoint). Aucun nouveau module ni nouvelle dépendance.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be
> justified**

Aucune violation à justifier — section omise.
