# Feature Specification: Vectorisation JSON via Mistral Embed

**Feature Branch**: `001-vectorisation-mistral-embed`

**Created**: 2026-10-06

**Status**: Draft

**Input**: User description: "Un outil de vectorisation à l'aide de l'API
Mistral AI : en input un ou plusieurs JSON d'index de chunks (ou un dossier),
en output une matrice NumPy ordonnée par chunk, avec batching, retry
exponentiel, reprise sur échec réseau, numérotation persistante des sorties,
et options CLI de configuration."

## Clarifications

### Session 2026-10-06

- Q: Que doit faire l'outil si on relance la vectorisation d'un JSON déjà
  complètement vectorisé avec succès ? → A: Nouveau fichier de sortie avec
  un nouveau numéro d'occurrence, à chaque exécution (pas de détection de
  doublon).
- Q: Quels échecs d'appel API doivent déclencher les retry, et lesquels
  doivent faire échouer immédiatement le document ? → A: Retry uniquement
  sur erreurs transitoires (réseau, timeout, saturation/429, erreurs
  serveur 5xx) ; échec immédiat pour les erreurs définitives (4xx hors
  429 : clé invalide, requête rejetée).
- Q: Si un document échoue puis est repris avec un modèle d'embedding
  différent de celui du premier essai, que doit faire l'outil de l'état de
  reprise sauvegardé ? → A: Invalider l'état de reprise et re-vectoriser
  le document depuis le premier lot, avec un message d'avertissement.
- Q: Que doit-il advenir du fichier d'état de reprise d'un document une
  fois sa matrice produite avec succès ? → A: Supprimer automatiquement
  le fichier d'état dès que la matrice est produite avec succès.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Vectoriser un JSON unique en matrice ordonnée (Priority: P1)

Un utilisateur lance la commande `vector` avec le chemin d'un JSON d'index
(schéma 1.0 : `schema_version`, `document`, `params`, `chunks`). L'outil
envoie les textes des chunks à l'API Mistral d'embedding (modèle
`mistral-embed`, 1024 dimensions, par défaut) et produit une matrice NumPy :
une ligne par chunk, une colonne par dimension du modèle. L'ordre des
lignes correspond exactement à l'ordre des chunks dans le JSON d'entrée.
Le fichier de sortie est enregistré dans le dossier de sortie, nommé selon
la règle : 20 premiers caractères du titre du document source, tiret,
numéro d'occurrence à 4 chiffres (ex. `Introduction aux Embeddi-0042.npy`).

**Why this priority**: C'est la valeur cœur de l'outil — transformer un
index JSON en embeddings exploitables pour un RAG. Sans cette story,
l'outil n'a aucune raison d'être.

**Independent Test**: Testable avec un seul JSON des `Examples/` : la
matrice produite a autant de lignes que de chunks et autant de colonnes
que la dimension du modèle choisi, dans l'ordre des `ref`.

**Acceptance Scenarios**:

1. **Given** un JSON valide au schéma 1.0, **When** l'utilisateur exécute
   `vector <chemin.json>`, **Then** un fichier de sortie est créé dans le
   dossier de sortie, contenant une matrice de dimensions (nombre de
   chunks x dimension du modèle).
2. **Given** un JSON contenant les chunks `ref` 1, 2, 3, **When** la
   vectorisation réussit, **Then** la ligne 1 de la matrice correspond au
   chunk 1, la ligne 2 au chunk 2, la ligne 3 au chunk 3 (correspondance
   stricte d'ordre, sans permutation).
3. **Given** un document source titré "Introduction aux Embeddings",
   **When** la sortie est produite, **Then** le nom du fichier de sortie
   commence par les 20 premiers caractères de ce titre, suivis de `-` et
   d'un numéro d'occurrence à 4 chiffres.
4. **Given** le compteur local d'occurrences est absent, **When** l'outil
   produit son premier document, **Then** le numéro d'occurrence utilisé
   est `0001`.
5. **Given** le compteur local existe et vaut 0041, **When** un document
   est produit, **Then** il porte le numéro `0042` et le compteur est mis
   à jour à 0042 avant tout autre traitement.
6. **Given** le fichier de compteur est présent mais illisible ou
   corrompu, **When** l'outil démarre, **Then** il échoue rapidement avec
   un message explicite et n'écrit aucune sortie.

---

### User Story 2 - Traiter plusieurs JSON ou un dossier (Priority: P2)

Un utilisateur fournit plusieurs chemins de JSON, ou un dossier. L'outil
détecte automatiquement la nature de l'input (un fichier, plusieurs
fichiers, un dossier) — c'est transparent pour l'utilisateur. Chaque JSON
est traité indépendamment selon le processus d'un seul : N inputs = N
sorties, toutes enregistrées dans le même dossier de sortie. Les fichiers
non-JSON dans un dossier sont ignorés.

**Why this priority**: Évite à l'utilisateur de lancer N fois la commande
pour un corpus ; c'est le cas d'usage réel (4 exemples fournis, en
pratique des dizaines de documents).

**Independent Test**: Testable avec le dossier `Examples/` (4 JSON) : une
seule invocation produit 4 matrices dans le dossier de sortie.

**Acceptance Scenarios**:

1. **Given** un dossier contenant 4 fichiers JSON et 2 fichiers non-JSON,
   **When** l'utilisateur passe le dossier en input, **Then** seuls les 4
   JSON sont traités et 4 sorties sont produites ; les fichiers non-JSON
   sont ignorés sans erreur.
2. **Given** plusieurs chemins de JSON passés en argument, **When**
   l'outil s'exécute, **Then** chaque JSON produit sa propre matrice,
   indépendamment des autres (l'échec d'un JSON n'empêche pas le
   traitement des suivants).
3. **Given** un dossier ne contenant aucun JSON valide, **When** l'outil
   s'exécute, **Then** il signale clairement qu'aucun input traitable n'a
   été trouvé, sans produire de sortie ni consommer de numéro
   d'occurrence.
4. **Given** un input multiple de 3 JSON, **When** les 3 documents sont
   produits, **Then** ils portent 3 numéros d'occurrence consécutifs,
   attribués dans l'ordre de traitement, sans doublon.

---

### User Story 3 - Pannes réseau : batch, retry et reprise (Priority: P3)

Pendant la vectorisation d'un document de 100 chunks (batchs de 25), le
3e lot échoue pour cause de réseau. L'outil retente automatiquement le
lot avec un délai exponentiel (1er essai après 3 s, puis 6 s, puis 12 s —
délai doublé à chaque essai), jusqu'à 3 essais par échec. Si le lot
échoue après épuisement des essais, l'état d'avancement du document est
sauvegardé : l'utilisateur peut relancer et reprendre à partir du lot
échoué, sans recalculer les lots déjà réussis.

**Why this priority**: La robustesse réseau conditionne la fiabilité sur
de gros corpus ; sans elle, un échec au lot 3 sur 4 force à tout
recalculer et à repayer des appels API.

**Independent Test**: Testable en simulant l'échec du 3e lot sur un
document de 100 chunks : après reprise, seuls les lots 3 et 4 font
l'objet de nouveaux appels API.

**Acceptance Scenarios**:

1. **Given** 100 chunks et une taille de batch de 25, **When** le
   traitement réussit, **Then** les appels API sont regroupés en 4 lots
   de 25.
2. **Given** un lot en échec transitoire, **When** les retry sont
   épuisés avec succès au 2e essai, **Then** le traitement continue sans
   perte de données et sans doublon dans la matrice.
3. **Given** un lot définitivement en échec après tous les essais,
   **When** l'utilisateur relance l'outil sur le même JSON, **Then** la
   reprise repart du lot échoué : les lots déjà vectorisés ne sont pas
   renvoyés à l'API.
4. **Given** `--taille-batch 0`, **When** le document est traité,
   **Then** aucun regroupement n'est effectué : les chunks sont envoyés
   en requêtes simples, sans batch.
5. **Given** `--retry-occurences` à 5 et `--retry-time` à 2, **When** un
   lot échoue, **Then** l'outil retente jusqu'à 5 fois, le premier essai
   après 2 s, puis en doublant le délai à chaque essai (2, 4, 8, 16,
   32 s).

---

### User Story 4 - Configurer l'outil via la ligne de commande (Priority: P4)

L'utilisateur peut ajuster le comportement via des options :
`--choix-techno` (modèle d'embedding parmi `mistral-embed` / 1024 dim par
défaut, `mistral-embed-dim256-2510` / 256 dim, `mistral-embed-dim128-2510`
/ 128 dim), `--taille-batch` (0 à 100, 25 par défaut),
`--retry-occurences` (0 à 10, 3 par défaut), `--retry-time` (1 à 10 s, 3
par défaut), `--output-folder` (chemin de sortie, `output` à la racine par
défaut). La clé API n'est jamais passée en argument : elle vit uniquement
dans la variable d'environnement `MISTRAL_API_KEY`.

**Why this priority**: Les défauts couvrent l'usage standard ; la
configuration sert les cas avancés (latence réduite via 256 dim,
environnement contraint via 128 dim).

**Independent Test**: Testable en invoquant `vector` avec chaque option
et en vérifiant l'effet sur la sortie (dimensions de la matrice, taille
des lots, délais de retry, emplacement des fichiers).

**Acceptance Scenarios**:

1. **Given** `--choix-techno mistral-embed-dim256-2510`, **When** un
   document est vectorisé, **Then** la matrice de sortie compte 256
   colonnes et le nom du modèle utilisé dans la requête API est
   `mistral-embed-dim256-2510`.
2. **Given** aucun choix de modèle, **When** un document est vectorisé,
   **Then** le modèle `mistral-embed` (1024 dimensions) est utilisé par
   défaut.
3. **Given** `--output-folder mon_dossier`, **When** la sortie est
   produite, **Then** les fichiers sont enregistrés dans `mon_dossier`
   (créé si absent) ; en son absence, ils vont dans `output` créé à la
   racine du projet.
4. **Given** une option hors bornes (ex. `--taille-batch 150`), **When**
   l'outil démarre, **Then** il échoue rapidement avec un message
   explicite.
5. **Given** la variable d'environnement `MISTRAL_API_KEY` absente ou
   vide, **When** l'outil démarre, **Then** il échoue rapidement avec un
   message explicite, avant tout appel API.
6. **Given** l'ensemble d'une exécution, **When** l'outil écrit des
   fichiers (sorties, logs, état de reprise), **Then** la clé API
   n'apparaît dans aucun d'eux.

### Edge Cases

- Que se passe-t-il si le titre du document fait moins de 20 caractères ?
  Le nom de sortie utilise le titre en entier (troncature au plus court).
- Que se passe-t-il si le titre contient des caractères invalides pour un
  nom de fichier ? Ils sont neutralisés (remplacés/supprimés) pour
  garantir un nom de fichier valide.
- Comment le système gère-t-il un JSON invalide, illisible, ou non
  conforme au schéma 1.0 ? Échec rapide avec message explicite pour ce
  fichier ; les autres inputs d'une exécution multi-input sont traités
  normalement.
- Comment le système gère-t-il un JSON valide sans chunks (liste vide) ?
  Signalement explicite, aucune matrice produite pour ce document, aucun
  numéro d'occurrence consommé.
- Comment le système gère-t-il le passage à 9999 ? Le numéro d'occurrence
  suit un cycle : premier usage à 0001, progression d'une unité par
  document, retour à 0000 après 9999, puis nouveau cycle à 0001.
- Comment le système gère-t-il une interruption brutale (kill, panne) en
  cours de document ? Les numéros déjà consommés ne sont jamais réutilisés
  (compteur persisté après chaque document) ; les lots déjà réussis sont
  récupérables via l'état de reprise.
- Comment le système gère-t-il un JSON dont les chunks produiraient plus
  de lots que la limite d'un appel API ? Le lot est l'unité de découpe
  retenue (1 à 100 chunks par lot), inchangée par ailleurs.
- Que se passe-t-il si deux exécutions produisent le même titre ? Les
  numéros d'occurrence distincts garantissent l'absence de collision de
  noms au sein des exécutions.
- Comment le système gère-t-il la relance d'un JSON déjà complètement
  vectorisé avec succès ? Un nouveau document est produit avec un
  nouveau numéro d'occurrence, consommé à chaque exécution ; aucune
  détection de doublon ni écrasement de la sortie existante.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: L'outil DOIT exposer une commande générale `vector`
  acceptant en input un chemin de JSON, plusieurs chemins de JSON, ou un
  dossier — la nature de l'input (un, plusieurs, dossier) DOIT être
  détectée automatiquement, sans option supplémentaire.
- **FR-002**: Lorsque l'input est un dossier, l'outil DOIT ignorer tout
  fichier non-JSON et ne traiter que les fichiers `.json`.
- **FR-003**: En multi-input, l'outil DOIT traiter chaque JSON
  indépendamment selon le processus d'un input unique (N inputs = N
  sorties), et enregistrer toutes les sorties dans le même dossier de
  sortie.
- **FR-004**: Pour chaque JSON, l'outil DOIT produire une matrice NumPy
  où chaque ligne correspond au chunk d'entrée de même rang et chaque
  colonne à une dimension du modèle d'embedding choisi.
- **FR-005**: L'ordre d'enregistrement des vecteurs dans la matrice DOIT
  correspondre exactement à l'ordre des chunks dans le JSON d'entrée
  (correspondance stricte ligne i ↔ chunk i, sans permutation ni perte).
- **FR-006**: L'outil DOIT supporter trois modèles d'embedding, le choix
  déterminant à la fois le nom de modèle utilisé dans la requête API et
  la dimension (nombre de colonnes) de la matrice : `mistral-embed`
  (1024 dimensions, défaut), `mistral-embed-dim256-2510` (256
  dimensions), `mistral-embed-dim128-2510` (128 dimensions). Le modèle
  `mistral-embed` à 1024 dimensions DOIT être utilisé par défaut.
- **FR-007**: L'outil DOIT regrouper les chunks en lots pour les requêtes
  API, avec une taille de lot par défaut de 25. L'option `--taille-batch`
  DOIT permettre de fixer cette taille entre 0 et 100 ; la valeur 0 DOIT
  désactiver le batching (requêtes simples, sans regroupement).
- **FR-008**: En cas d'échec d'une requête ou d'un lot, l'outil DOIT
  retenter avec un délai exponentiel : nombre d'essais configurable via
  `--retry-occurences` (entre 0 et 10, 3 par défaut), premier délai
  configurable via `--retry-time` (entre 1 et 10 secondes, 3 par
  défaut), délai doublé à chaque essai (ex. 3, 6, 12 secondes pour la
  configuration par défaut). Le retry s'applique uniquement aux erreurs
  transitoires (indisponibilité réseau, timeout, saturation de l'API /
  429, erreurs serveur 5xx) ; une erreur définitive (4xx hors 429 : clé
  invalide, requête rejetée) DOIT faire échouer immédiatement le document
  avec un message explicite, sans consommer les essais.
- **FR-009**: L'outil DOIT sauvegarder l'état d'avancement de chaque
  document (lots réussis) de sorte qu'après un échec réseau ou une
  interruption, la reprise reparte du lot échoué sans recalculer les
  lots déjà vectorisés — y compris entre deux exécutions de l'outil.
  L'état de reprise DOIT être lié au modèle d'embedding utilisé : si le
  modèle change entre deux tentatives sur un même document, l'état DOIT
  être invalidé et le document re-vectorisé depuis le premier lot, avec
  un message d'avertissement.
- **FR-010**: Le nom de chaque matrice de sortie DOIT être composé des
  20 premiers caractères du titre du document source (champ
  `document.title` du JSON), suivis d'un tiret `-`, suivis d'un numéro
  d'occurrence à 4 chiffres.
- **FR-011**: Le numéro d'occurrence DOIT être attribué à chaque
  document produit, dans l'ordre de création, sans doublon au sein d'une
  exécution. Le dernier numéro utilisé DOIT être mémorisé dans un
  fichier texte à la racine de l'outil, contenant uniquement ce numéro,
  et persisté après chaque document produit : un numéro consommé n'est
  jamais réutilisé, même en cas d'interruption de l'exécution.
- **FR-012**: Le numéro d'occurrence DOIT suivre un cycle : premier usage
  à 0001, progression d'une unité par document, retour à 0000 après
  9999, puis nouveau cycle.
- **FR-013**: Si le fichier de compteur est absent, l'outil DOIT
  repartir à 0001 ; s'il est présent mais illisible ou corrompu, l'outil
  DOIT échouer rapidement avec un message explicite, sans écrire de
  sortie.
- **FR-014**: L'outil DOIT, par défaut, créer si nécessaire un dossier
  `output` à la racine du projet et y inscrire les sorties ; l'option
  `--output-folder` DOIT permettre de proposer un chemin de sortie
  alternatif (créé si absent).
- **FR-015**: La clé d'appel API DOIT être chargée depuis la variable
  d'environnement `MISTRAL_API_KEY` (fichier `.env` local, exclu du
  contrôle de version). L'outil DOIT la lire uniquement pour les appels
  API d'embedding et il lui est FORMELLEMENT INTERDIT de la copier,
  l'écrire ou l'afficher où que ce soit (code, config, logs, sorties,
  exemples).
- **FR-016**: L'outil DOIT valider ses entrées au lancement et échouer
  rapidement avec un message explicite (sans écrire de sortie ni
  consommer de numéro d'occurrence) si : la clé API est absente, un JSON
  est invalide ou non conforme au schéma 1.0, ou une option reçoit une
  valeur hors bornes.
- **FR-017**: Les seuls appels réseau autorisés DOIVENT être ceux de
  l'API d'embedding Mistral pour les chunks traités ; aucun autre trafic
  sortant (télémétrie, sync, mise à jour) n'est permis, conformément à
  la Constitution du projet.

### Key Entities *(include if feature involves data)*

- **JSON d'index (input)**: Fichier au schéma 1.0 — `schema_version`,
  `document` (dont `title`, source du nom de sortie), `params`
  (paramètres de découpage, non interprétés), `chunks` (liste ordonnée).
  Unité d'entrée du processus, un input = un traitement indépendant.
- **Chunk**: Fragment de texte d'un document source, portant `ref`
  (rang séquentiel), `text` (contenu vectorisé), `length`, `boundary`,
  `part`, `page` (optionnel), `position_in_part`, `atomic`. Son rang
  dans `chunks` fixe sa ligne dans la matrice.
- **Modèle d'embedding (preset)**: Association nom de modèle API /
  dimension de sortie — `mistral-embed`/1024 (défaut),
  `mistral-embed-dim256-2510`/256, `mistral-embed-dim128-2510`/128.
  Détermine le nom utilisé dans la requête API et le nombre de colonnes
  de la matrice.
- **Lot (batch)**: Groupe de chunks envoyés en une seule requête API
  (1 à 100 chunks, 25 par défaut). Unité de découpe, de retry et de
  reprise.
- **Matrice de sortie**: Matrice NumPy (nombre de chunks x dimension du
  modèle), une ligne par chunk dans l'ordre exact du JSON d'entrée ;
  nommée par titre tronqué + numéro d'occurrence ; enregistrée dans le
  dossier de sortie.
- **Compteur d'occurrence**: Dernier numéro d'occurrence utilisé,
  persisté dans un fichier texte à la racine de l'outil ; cycle
  0001→9999→0000→0001 ; source de vérité unique pour l'unicité des
  noms de sortie.
- **État de reprise (checkpoint)**: Sauvegarde locale des lots déjà
  vectorisés par document en cours de traitement, permettant de
  reprendre au lot échoué sans recalculer les lots réussis. Lié au
  modèle d'embedding ; supprimé dès que la matrice du document est
  produite avec succès.
- **Clé API**: Identifiant Mistral chargé depuis l'environnement
  (`MISTRAL_API_KEY`), utilisé uniquement pour les appels d'embedding,
  jamais persisté ni affiché.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Pour tout JSON d'entrée traité, 100 % des chunks figurent
  dans la matrice de sortie, dans l'ordre exact du JSON (vérifiable
  ligne à ligne sur les 4 exemples fournis).
- **SC-002**: Un dossier de 4 JSON produit 4 matrices dans le dossier de
  sortie en une seule invocation, avec 4 numéros d'occurrence
  consécutifs et sans doublon.
- **SC-003**: Sur un document de 100 chunks dont le 3e lot échoue, la
  reprise ne renvoie à l'API que les lots non encore réussis (aucun
  recalcul des lots 1 et 2).
- **SC-004**: Un échec réseau transitoire (rétabli dans le budget de
  retry) n'entraîne aucun échec de document : 100 % des documents avec
  pannes transitoires sont produits.
- **SC-005**: Sur une série de 10 exécutions successives, y compris avec
  interruptions volontaires, aucun numéro d'occurrence n'est réutilisé
  (vérifiable via le fichier compteur et les fichiers de sortie).
- **SC-006**: La clé API n'apparaît dans aucun fichier écrit par l'outil
  (sorties, logs, état de reprise, compteur) — vérifiable par
  inspection.
- **SC-007**: Chaque matrice produite respecte la règle de nommage (20
  premiers caractères du titre + `-` + numéro à 4 chiffres) et la
  dimension du modèle choisi (1024, 256 ou 128 colonnes).
- **SC-008**: Toute condition d'erreur (JSON invalide, compteur
  corrompu, clé absente, option hors bornes) aboutit à un échec rapide
  avec un message explicite, sans fichier de sortie parasite.

## Assumptions

- Les JSON d'input respectent le schéma 1.0 décrit (les 4 exemples de
  `Examples/` en sont la référence) ; les champs `params` sont lus mais
  non interprétés par l'outil.
- Le titre du `.md` d'entrée est disponible via `document.title` du
  JSON ; s'il comporte moins de 20 caractères, il est pris en entier ;
  les caractères interdits dans un nom de fichier sont neutralisés.
- La matrice de sortie est persistée sous forme de fichier NumPy
  (`.npy`), un fichier par document traité.
- "Requête embedding simple" (`--taille-batch 0`) signifie une requête
  par chunk, sans regroupement.
- L'état de reprise est persistant (fichiers locaux), ce qui permet la
  reprise y compris après arrêt/redémarrage de l'outil, et pas
  seulement en cours d'exécution. Le fichier d'état est supprimé
  automatiquement dès que la matrice du document est produite avec
  succès (aucune copie cachée conservée, conformément à la
  Constitution) ; il n'est conservé que pour les documents interrompus
  ou en échec.
- Les textes des chunks sont transmis à l'API Mistral d'embedding —
  c'est le seul trafic sortant, explicitement demandé par l'utilisateur ;
  tout le reste (sorties, compteur, état de reprise) reste strictement
  local, conformément à la Constitution.
- Le fichier `.env` contenant `MISTRAL_API_KEY` est fourni par
  l'utilisateur et exclu du contrôle de version ; un template avec
  placeholder peut être commité, jamais une clé réelle.
- En multi-input, l'échec d'un document n'interrompt pas le traitement
  des suivants ; en revanche un compteur corrompu interrompt toute
  l'exécution (fail-fast global).
- L'ordre de traitement des JSON d'un dossier suit un ordre stable et
  prévisible (ex. tri alphabétique), afin que l'attribution des numéros
  d'occurrence soit déterministe.
