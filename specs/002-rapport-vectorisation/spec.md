# Feature Specification: Rapport de traçabilité optionnel (`--rapport`)

**Feature Branch**: `002-rapport-vectorisation`

**Created**: 2026-10-07

**Status**: Draft

**Input**: User description (handoff de
`.specify/assessments/rapport-vectorisation/decision.md`) : « Option B —
sidecar JSON par matrice, activé par une option booléenne `--rapport`
désactivée par défaut ; rapport portant le même nom que la matrice
(extension `.json`), avec cinq champs : entrée (document JSON source),
sortie (matrice `.npy`), embed (modèle), dimension, nature (dtype).
L'utilisateur du CLI `vector` ne peut pas, après coup, déterminer quel JSON
d'entrée, quel modèle et quelle dimension ont produit une matrice `.npy`
donnée ; la seule trace est console et éphémère, la perte est
irréversible. »

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Rapport de traçabilité par matrice (Priority: P1)

Un utilisateur lance la commande `vector` avec l'option `--rapport`. Chaque
document JSON traité avec succès produit, en plus de sa matrice `.npy`
habituelle, un rapport JSON portant exactement le même nom que la matrice
(extension `.json` mise). Ce rapport décrit le document d'entrée, la matrice
produite, le modèle d'embedding utilisé, la dimension des vecteurs et la
nature des nombres flottants qui composent la matrice. L'utilisateur peut
ainsi, des semaines plus tard et sans console, savoir quel document et quels
paramètres ont produit n'importe quelle matrice de son dossier de sortie.

**Why this priority**: C'est la valeur cœur de la feature — la traçabilité
durable matrice → (document source, modèle, dimension). Sans cette story,
la feature n'a aucune raison d'être.

**Independent Test**: Testable avec un JSON des `Examples/` : après
exécution avec `--rapport`, le dossier de sortie contient, pour chaque
matrice produite, un fichier JSON de même nom dont les cinq champs sont
cohérents avec l'exécution (document traité, nom de la matrice, modèle
choisi, dimension du modèle, type des flottants).

**Acceptance Scenarios**:

1. **Given** un JSON valide traité avec succès avec l'option `--rapport`,
   **When** la matrice est écrite, **Then** un rapport JSON est écrit dans
   le même dossier de sortie, portant le même nom que la matrice
   (extension `.json` remplacée).
2. **Given** le rapport de la matrice `016472351681860015-0042.npy`,
   **When** l'utilisateur l'ouvre, **Then** il y lit le nom du fichier JSON
   d'entrée, le nom de la matrice, l'identifiant du modèle d'embedding, la
   dimension des vecteurs et la nature des flottants de la matrice.
3. **Given** l'option `--rapport` combinée à `--choix-techno
   mistral-embed-dim256-2510`, **When** un document réussit, **Then** le
   rapport indique ce modèle et la dimension 256.

---

### User Story 2 - Comportement par défaut strictement inchangé (Priority: P2)

Un utilisateur lance la commande `vector` sans l'option `--rapport`. Rien ne
change pour lui : exactement un fichier `.npy` par document réussi, mêmes
messages console, mêmes codes de sortie, aucun fichier supplémentaire dans
le dossier de sortie. L'opt-in strict garantit que la feature ne peut pas
altérer les usages et scripts existants.

**Why this priority**: C'est la métrique de sécurité de la feature — sans
elle, la feature devient un risque de régression pour le parc d'usages
existants.

**Independent Test**: Testable en rejouant une exécution identique sans
l'option et en comparant le contenu du dossier de sortie, les messages
console et le code de sortie au comportement antérieur.

**Acceptance Scenarios**:

1. **Given** une exécution de `vector` sans `--rapport`, **When** N
   documents réussissent, **Then** le dossier de sortie contient
   exactement N fichiers `.npy` et aucun fichier JSON de rapport.
2. **Given** une exécution sans `--rapport` où des documents échouent,
   **When** l'exécution se termine, **Then** les codes de sortie et les
   messages console sont identiques à ceux du comportement antérieur à la
   feature.

---

### User Story 3 - Lot multi-documents avec échecs partiels (Priority: P3)

Un utilisateur lance `vector` avec `--rapport` sur plusieurs JSON (ou un
dossier). Chaque document réussi reçoit sa matrice et son rapport ; chaque
document en échec ne produit ni matrice ni rapport, et l'échec est signalé
en console comme aujourd'hui. Le lot continue après un échec documentaire.

**Why this priority**: Complète la story 1 pour le cas d'usage multi-input
réel ; sans elle, le comportement en échec partiel serait indéfini.

**Independent Test**: Testable avec un lot contenant un JSON invalide et un
JSON valide : un rapport est produit pour le valide, aucun pour l'invalide,
le code de sortie reflète l'échec.

**Acceptance Scenarios**:

1. **Given** un lot de 3 documents dont 1 en échec définitif, **When**
   l'exécution avec `--rapport` se termine, **Then** 2 rapports existent,
   un par matrice réussie, et aucun rapport pour le document échoué.
2. **Given** un document échoue après consommation d'un numéro
   d'occurrence, **When** le rapport d'un autre document réussi est
   écrit, **Then** les numéros d'occurrence des rapports correspondent
   à ceux de leurs matrices respectives.

---

### Edge Cases

- Que se passe-t-il si l'utilisateur pointe `--output-folder` vers le
  dossier contenant les JSON d'entrée ? Les rapports portent le nom des
  matrices (`<stem>-<NNNN>.json`), jamais le nom d'un JSON d'entrée
  (`<stem>.json`) : aucun écrasement possible ; l'écriture est autorisée
  sans avertissement dédié.
- Que se passe-t-il si l'utilisateur re-vectorise un document déjà traité ?
  Un nouveau numéro d'occurrence est consommé : la nouvelle matrice et le
  nouveau rapport ont des noms distincts, l'ancien rapport n'est ni
  modifié ni supprimé (rétention contrôlée par l'utilisateur, comme les
  matrices).
- Que se passe-t-il si le rapport ne peut pas être écrit (disque plein,
  droits insuffisants) alors que la matrice a été écrite ? Le document est
  compté en échec avec un message explicite ; la matrice déjà écrite est
  conservée ; l'exécution continue selon les règles multi-input
  existantes.
- Que se passe-t-il si le compteur d'occurrences est corrompu ? Arrêt
  global avant toute écriture (matrice ou rapport), inchangé.
- Que se passe-t-il si l'état de reprise (checkpoint) d'un document est
  réutilisé avec succès ? Le rapport décrit l'exécution qui a produit la
  matrice finale ; l'historique des lots repris n'y figure pas.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Le CLI `vector` DOIT accepter une option booléenne
  `--rapport`, désactivée par défaut, activant la production des rapports
  de traçabilité.
- **FR-002**: Sans l'option `--rapport`, le CLI NE DOIT produire aucun
  fichier de rapport : sorties, messages console et codes de sortie
  strictement identiques au comportement sans la feature.
- **FR-003**: Avec l'option `--rapport`, le système DOIT écrire, pour
  chaque matrice produite avec succès, un rapport JSON dans le même
  dossier de sortie, portant exactement le même nom que la matrice avec
  l'extension `.json`.
- **FR-004**: Chaque rapport DOIT contenir, pour le document concerné :
  le nom du fichier JSON d'entrée (champ « entrée »), le nom du fichier
  matrice produit (champ « sortie »), l'identifiant du modèle d'embedding
  utilisé (champ « embed »), la dimension des vecteurs (champ
  « dimension ») et la nature des flottants de la matrice (champ
  « nature »).
- **FR-005**: Le champ « entrée » DOIT contenir le nom du fichier JSON
  d'entrée seul, sans chemin absolu (aucune information sur la machine de
  l'utilisateur ne doit fuiter dans le rapport).
- **FR-006**: Le champ « embed » DOIT contenir l'identifiant exact du
  modèle tel que passé à l'option `--choix-techno` ; le champ
  « dimension » DOIT contenir la dimension de ce modèle ; le champ
  « nature » DOIT contenir le type des flottants de la matrice écrite.
- **FR-007**: Un rapport NE DOIT être écrit qu'après l'écriture réussie
  de la matrice correspondante.
- **FR-008**: Un document en échec NE DOIT produire ni matrice ni
  rapport ; les autres documents du lot continuent d'être traités et
  reçoivent leurs rapports selon les règles existantes.
- **FR-009**: Un rapport NE DOIT jamais contenir de clé API, de
  credential, de chemin absolu ni aucune donnée sensible (Constitution
  I et II).
- **FR-010**: L'écriture d'un rapport NE DOIT déclencher aucun appel
  réseau ; la feature est intégralement locale et testable hors ligne
  (Constitution II).
- **FR-011**: Si l'écriture d'un rapport échoue alors que la matrice a
  été écrite, le système DOIT compter le document en échec avec un
  message explicite et poursuivre le lot selon les règles multi-input.
- **FR-012**: L'option `--rapport` DOIT être validée avec les autres
  options avant tout appel API, selon les règles d'échec rapide
  existantes (aucun numéro d'occurrence consommé par une validation).

### Key Entities *(include if feature involves data)*

- **Rapport de traçabilité**: fichier JSON sidecar d'une matrice `.npy`,
  de même nom ; cinq attributs décrivant l'exécution qui a produit la
  matrice — entrée (nom du JSON source), sortie (nom de la matrice),
  embed (modèle), dimension (taille des vecteurs), nature (type des
  flottants) ; durée de vie identique à celle de la matrice (rétention
  contrôlée par l'utilisateur dans le dossier de sortie).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Pour 100 % des documents traités avec succès avec l'option
  `--rapport` activée, la correspondance matrice → (document source,
  modèle, dimension) est vérifiable en lisant uniquement le rapport,
  sans ouvrir la matrice ni disposer de la console de l'exécution.
- **SC-002**: Sans l'option `--rapport`, toute exécution produit des
  sorties, des messages et des codes de sortie identiques à ceux de
  l'outil avant la feature (vérifiable par la suite de tests existante,
  sans réseau).
- **SC-003**: Par défaut, exactement 1 fichier `.npy` est produit par
  document réussi et aucun fichier supplémentaire n'apparaît dans le
  dossier de sortie ; avec l'option activée, exactement 2 fichiers
  (matrice + rapport) par document réussi.
- **SC-004**: Aucun rapport produit ne contient de clé API ni de chemin
  absolu (vérifiable par inspection des rapports produits en test).

## Assumptions

- Le consommateur du rapport est une lecture humaine ou un script
  simple : un JSON plat à cinq champs suffit ; pas de schéma versionné,
  pas d'horodatage, pas de métadonnée d'exécution (lot, durées, coûts).
- Le champ « entrée » est le nom du fichier du JSON d'entrée (nom seul,
  pas de chemin), conformément au FR-005 ; les cinq noms de champs sont
  ceux de l'intake d'origine.
- Le champ « embed » est l'identifiant du preset CLI (`mistral-embed`,
  `mistral-embed-dim256-2510`, `mistral-embed-dim128-2510`), identique à
  la valeur passée à `--choix-techno`.
- La nature des flottants est aujourd'hui constante (float 32 bits) ;
  le champ est néanmoins inclus par commodité, pour rester vrai si le
  type change un jour.
- Les rapports suivent la même politique de rétention que les matrices :
  l'utilisateur les supprime ou les conserve librement ; l'outil n'en
  garde aucune copie cachée (Constitution, Data Retention).
- Un échec d'écriture de rapport n'efface pas la matrice déjà écrite
  (le coût API est dépensé) ; le document est compté en échec.
- La rétro-documentation des matrices déjà présentes dans `output/`
  avant la feature est hors périmètre : leur provenance est définitivement
  perdue.
