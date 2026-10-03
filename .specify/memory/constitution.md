<!--
Sync Impact Report - Constitution v1.3.0
=========================================
Version change: 1.0.0 -> 1.3.0 (MINOR: 3 amendments added)
Added sections: Amendments (1-3), Automated Compliance Checks in Development
Workflow
Modified principles: N/A
Removed sections: N/A
Follow-up TODOs: None
-->

# Vectorizator Constitution

## Core Principles

### I. Isolation des secrets (NON NÉGOCIABLE)

Aucune clé API, token ou identifiant ne doit figurer dans le code source, la
configuration, les tests ou tout fichier commité. Les identifiants sont chargés
à l'exécution depuis des variables d'environnement ou un fichier de config
local exclu par .gitignore. Seuls des placeholders (YOUR_API_KEY, DATA_DIR)
sont autorisés dans les exemples.

Rationale: Prévenir les fuites de données sensibles via le contrôle de version
et assurer la sécurité par défaut.

### II. Local-first & confidentialité (NON NÉGOCIABLE)

Toutes les données, résultats et logs restent sur la machine locale : pas de
cloud, pas de base distante, pas de sync tiers. Le fonctionnement hors-ligne
doit être possible pour les parties locales (parsing, stockage).

Rationale: Garantir la souveraineté des données et le respect de la vie privée
des utilisateurs.

### III. Open-source & sans trackers

Toutes les dépendances d'exécution doivent être open-source et sans
trackers/télémétrie. Licences permissives privilégiées (MIT, Apache-2.0, BSD)
pour rester compatibles avec la licence MIT du projet.

Rationale: Assurer la transparence, l'auditabilité et la compatibilité avec la
philosophie open-source du projet.

### IV. Simplicité (YAGNI)

Toute fonctionnalité au coeur de l'outil doit être justifiée. Pas d'abstraction
prématurée, pas de plugins, pas de multi-tenant. Un point d'entrée CLI est
préféré à un serveur web ou GUI.

Rationale: Maintenir un codebase minimal, maintenable et axé sur le besoin réel.

## Security & Privacy Requirements

### Secrets Management

Clés et tokens fournis uniquement via variables d'environnement ou config
git-ignorée. Un template config.example.* avec placeholders peut être commité,
jamais la config réelle.

### Path Isolation

Les répertoires de données et de résultats sont résolus depuis la config
locale, jamais codés en dur. Les valeurs par défaut éventuelles doivent être
des chemins relatifs ou des placeholders clairement marqués.

### No Cloud

Aucun upload, sync ou backup vers un service cloud n'est autorisé.

### No Trackers

Aucun SDK d'analytics, télémétrie ou crash-reporting n'est autorisé. Les
dépendances sont auditées avant adoption.

### Network Surface

Les appels sortants sont limités à l'URL demandée par l'utilisateur. Aucun
autre trafic sortant n'est autorisé.

### Data Retention

L'utilisateur contrôle la rétention en supprimant les fichiers du répertoire de
sortie. Le tool ne doit conserver aucune copie cachée.

## Development Workflow

### Config Validation

Le tool doit valider au lancement que la configuration et les chemins requis
sont présents et échouer rapidement avec un message clair. Interdiction de
recourir à des défauts codés en dur pour les secrets ou chemins personnels.

### Commit Hygiene

Avant tout commit, vérification qu'aucune clé réelle ni chemin personnel n'est
dans le diff. Le .gitignore doit couvrir les configs locales et répertoires de
sortie.

### Automated Compliance Checks

Un workflow GitHub Actions (`diagnostic.yml`) vérifie automatiquement la
conformité à cette constitution sur chaque `push`, `pull_request` et via un
cron hebdomadaire.

- **Job `constitution-compliance`** : Vérifie les principes I et II
  (secrets, local-first) en mode fail-fast.
- **Job `secrets`** : Détecte les fuites de secrets avec Gitleaks
  v8.21.2 (MIT).
- **Job `lint`** : Applique Ruff v0.16.8 (MIT) et markdownlint-cli2
  (MIT) pour le style de code.
- **Job `workflows-security`** : Audite les workflows avec Zizmor
  (Apache-2.0) et actionlint v1.7.3 (MIT).
- **Job `audit`** (hebdomadaire) : Scanne les vulnérabilités avec
  Trivy (Apache-2.0) et pip-audit (MIT).
Tous les outils sont open-source (conforme à III) et
s'exécutent sans
transmettre de données utilisateur (conforme à II).

## Additional Requirements

### Sovereign Tools Preference

Les outils et packages utilisés doivent, dans la mesure du possible, être
souverains : création et hébergement en Europe ou en France.

## Governance

La Constitution prime sur toutes les autres pratiques et documents du projet.
Tout amendement doit être documenté, approuvé et accompagné d'un plan de
migration si nécessaire. La compliance avec cette Constitution doit être
vérifiée pour chaque PR et review. Les principes marqués NON NÉGOCIABLE ne
peuvent être modifiés qu'avec l'accord unanime de tous les mainteneurs.

## Amendments

### Amendment 1 — GitHub Token pour l'audit de sécurité des workflows

**Date** : 2026-09-28 | **Status** : Ratified

**Modification** :
L'usage de `secrets.GITHUB_TOKEN` est **explicitement permis** pour le seul but
d'exécuter **Zizmor** dans un job dédié du workflow GitHub Actions, sous les
conditions strictes suivantes :

- **Purpose** : Uniquement pour auditer la sécurité des fichiers workflows
  (ex: `.github/workflows/*.yml`).
- **Scope** : Le token doit être restreint à **`contents: read`**
  et aucune autre permission.
- **No Data Transmission** : Le token ne doit **pas** transmettre de
  données utilisateur, de contenus traités par Vectorizator,
  ou d'informations personnelles à GitHub ou tout tiers.
- **Tool Limitation** : Seul Zizmor (open-source, Apache-2.0) peut
  utiliser ce token. Aucun autre outil, script ou étape de workflow.
- **Audit Trail** : Toutes les utilisations du token doivent être
  loguées dans la sortie du workflow, et le workflow doit échouer
  si le token est utilisé à d'autres fins.

**Rationale** :
L'audit de sécurité des workflows est un **contrôle critique** pour appliquer
les principes **I** (Isolation des secrets) et **II** (Local-first &
confidentialité) au niveau CI/CD. Zizmor nécessite des permissions minimales
(`contents: read`) pour analyser les fichiers workflows sans exposer de données
utilisateur ni violer le principe Local-first.

**Previous Version** : 1.0.0 | **New Version** : 1.1.0

---

### Amendment 2 — Appels réseau pour les outils CI/CD

**Date** : 2026-09-28 | **Status** : Ratified

**Modification** :
Les appels réseau sortants sont **explicitement permis** pour télécharger des
outils open-source CI/CD pendant l'exécution du workflow, sous les conditions
strictes suivantes :

- **Purpose** : Uniquement pour installer les outils requis par le
  workflow `diagnostic.yml`.
- **Authorized Tools** : Limités à **`npm`**, **`curl`**, **`pip`**,
  **`pipx`** pour télécharger les outils suivants :
  - `markdownlint-cli2` (MIT, via npm)
  - `gitleaks` (MIT, via curl)
  - `ruff` (MIT, via pip/pipx)
  - `zizmor` (Apache-2.0, via pipx)
  - `actionlint` (MIT, via curl)
  - `trivy` (Apache-2.0, via curl)
  - `pip-audit` (MIT, via pipx)
- **Scope** : Limité au workflow `diagnostic.yml` et à ses
  étapes.
- **No Data Transmission** : Ces appels ne doivent **pas**
  transmettre de données utilisateur, de contenus traités par
  Vectorizator, ou d'informations personnelles.
- **No Trackers** : Tous les outils téléchargés doivent être
  open-source, sans trackers ni télémétrie intégrés.

**Rationale** :
Les workflows CI/CD nécessitent des outils externes pour l'audit de sécurité
(Gitleaks, Trivy), le linting (Ruff, markdownlint-cli2) et l'audit des
dépendances (pip-audit). Ces outils sont **essentiels** pour appliquer les
principes **I** (Isolation des secrets), **III** (Open-source) et les exigences
de qualité. Les appels réseau sont isolés à l'environnement CI, utilisent
uniquement des outils open-source autorisés, et ne transmettent pas de données
utilisateur, respectant ainsi les principes fondamentaux du projet.

**Previous Version** : 1.1.0 | **New Version** : 1.2.0

---

### Amendment 3 — Vérifications automatisées de conformité

**Date** : 2026-09-28 | **Status** : Ratified

**Modification** :
Un workflow GitHub Actions (`diagnostic.yml`) est **explicitement autorisé**
pour vérifier automatiquement la conformité à cette constitution, sous les
conditions suivantes :

- **Déclencheurs** : Exécution sur `push` (branche `main`),
  `pull_request`, et via un cron hebdomadaire (`0 6 * * 1`).
- **Jobs** :
  - `constitution-compliance` : Vérifie les principes **I** et
    **II** (secrets, local-first) en mode **fail-fast**.
  - `secrets` : Détecte les fuites de secrets avec
    Gitleaks v8.21.2.
  - `lint` : Applique Ruff v0.16.8 et markdownlint-cli2
    pour le style de code.
  - `workflows-security` : Audite les workflows avec
    Zizmor et actionlint v1.7.3.
  - `audit` (hebdomadaire) : Scanne les vulnérabilités
    avec Trivy et pip-audit.
- **Scope** : Tous les outils utilisés sont open-source
  (conforme à **III**) et s'exécutent sans transmettre de
  données utilisateur (conforme à **II**).

**Rationale** :
L'automatisation de la conformité **renforce la gouvernance**
(section Governance : "La compliance [...] doit être vérifiée
pour chaque PR"). Ce workflow applique les principes **I** et
**II** au niveau CI/CD, en complément
des vérifications locales.

**Previous Version** : 1.2.0 | **New Version** : 1.3.0

---

### Amendment 4 — Hooks Pre-commit pour validation locale

**Date** : 2026-09-28 | **Status** : Ratified

**Modification** :
L'usage de **pre-commit** (open-source, MIT) est **explicitement permis** pour
le développement local, sous les conditions strictes suivantes :

- **Purpose** : Uniquement pour exécuter des **hooks locaux** afin
  d'appliquer les principes **I** et **II** avant tout commit.
- **Authorized Remote Hooks** : Seuls les dépôts open-source suivants sont
  autorisés :
  - `https://github.com/gitleaks/gitleaks` (MIT) — détection de secrets.
  - `https://github.com/astral-sh/ruff-pre-commit` (MIT) — linting et
    formatage Python.
  - `https://github.com/DavidAnson/markdownlint-cli2` (MIT) — linting
    Markdown.
- **Scope** : Limité au **développement local** (pas d'exécution dans GitHub
  Actions ou tout environnement CI distant).
- **No Data Transmission** : Les hooks ne doivent **pas**
  transmettre de données utilisateur, de contenus traités par
  Vectorizator, ou d'informations personnelles.
- **Network Calls** : L'installation initiale des hooks
  (`pre-commit install`) est autorisée **une seule fois par
  environnement développeur** pour la configuration.
  Les exécutions ultérieures utilisent les caches locaux.
- **Local First** : Tous les hooks doivent s'exécuter **localement** sur la
  machine du développeur. Aucune exécution dans le cloud n'est permise.

**Local Hooks** :

- `check_constitution.py --diff HEAD` — vérification des
  principes I et II.
- `audit_workflows.py .github/workflows/` — audit des workflows GitHub Actions.

**Exclusions** : Les scripts de vérification (`check_constitution.py`,
`audit_workflows.py`) sont **explicitement exclus** des checks qu'ils
exécutent, afin d'éviter des faux positifs (ex: détection du mot "cloud" dans
la liste `CLOUD_SERVICES` alors que le script vérifie justement l'absence de
services cloud).

**Rationale** :
Les hooks pre-commit sont un **contrôle critique** pour appliquer la
constitution **au plus tôt** (avant commit). Ils empêchent les secrets, le code
non conforme ou les appels réseau non autorisés d'entrer dans l'historique du
dépôt. En autorisant ces hooks open-source, les développeurs valident la
conformité localement, réduisant le risque de violations des principes **I** ou
**II** dans le dépôt distant. L'appel réseau unique pour l'installation
initiale est un compromis nécessaire pour une validation locale robuste, aligné
avec l'approche sécurité d'abord du projet.

**Previous Version** : 1.3.0 | **New Version** : 1.4.0

---

**Version**: 1.4.0 | **Ratified**: 2026-09-28 | **Last Amended**: 2026-09-28
