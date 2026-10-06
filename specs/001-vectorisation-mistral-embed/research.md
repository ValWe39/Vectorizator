# Research: Vectorisation JSON via Mistral Embed

Session 2026-10-06 — Phase 0. Aucun marqueur NEEDS CLARIFICATION ne
subsistait dans la spec ; les inconnues listées ci-dessous sont les choix
techniques à trancher avant le design. Toutes sont résolues.

Sources consultées : documentation locale fournie (« Ressources à
date/Mistral » : embedders-nettoye.md, batch-processing-nettoye.md ;
« Ressources à date/Corsen AI/consolidated.md » : appels embeddings,
batching, similarité) ; exemples réels `Examples/*.json` (schéma 1.0).

Règle de précédence (décision utilisateur, 2026-10-06) : en cas de
conflit entre le cours Corsen AI et la documentation officielle Mistral,
la documentation Mistral fait foi. À ce jour, aucune contradiction
n'a été relevée entre les deux sources (noms de modèles, dimensions et
endpoint identiques — cf. investigation du 2026-10-06) ; les méthodologies
diffèrent (sync direct vs abstractions async) sans s'opposer, et les choix
R-01/R-04/R-05 (appel sync direct) restent valables car compatibles avec
les deux sources.

## R-01 : Client d'appel API — SDK officiel `mistralai`

- Decision : SDK Python officiel `mistralai` (licence MIT).
- Rationale : `client.embeddings.create(model=..., inputs=[...])` renvoie
  `response.data[i].embedding` dans l'ordre des inputs — garantie d'ordre
  requise par FR-005 ; gère l'authentification par clé ; open-source,
  européen (préférence souveraine de la Constitution). Endpoint unique
  `/v1/embeddings` confirmé par la doc Mistral (batch-processing).
- Alternatives considered : appels HTTP bruts (`requests`) — rejeté :
  réimplémente auth et gestion d'erreurs sans bénéfice.

## R-02 : Chargement de la clé API

- Decision : `python-dotenv` charge le `.env` (déjà gitignoré) ; la clé
  n'existe qu'en variable d'environnement `MISTRAL_API_KEY` ; échec
  rapide et explicite si absente ou vide.
- Rationale : standard de facto, BSD, zéro réseau ; conforme
  Constitution I (isolation des secrets) et FR-015/FR-016.
- Alternatives considered : parsing manuel du `.env` — rejeté (moins
  robuste, aucune valeur ajoutée) ; clé en argument CLI — interdit.

## R-03 : Presets de modèles d'embedding

- Decision : mapping constant nom de modèle -> dimension :
  `mistral-embed` -> 1024 (défaut), `mistral-embed-dim256-2510` -> 256,
  `mistral-embed-dim128-2510` -> 128. La dimension renvoyée par l'API
  doit correspondre à la largeur de la matrice (contrôle en sortie).
- Rationale : confirmé par la doc Mistral locale (embedders-nettoye.md,
  table des constantes `MODEL_1024/256/128_EMBEDDING`).
- Alternatives considered : aucune — imposé par la spec (FR-006).

## R-04 : Batching

- Decision : lots de `--taille-batch` chunks (25 par défaut, 0 à 100 ;
  0 = une requête par chunk). Les réponses sont assemblées par `extend`
  pour garantir l'ordre ligne i <-> chunk i.
- Rationale : pattern du cours Corsen (consolidated.md, §Batching) :
  lot type de 25, plafond 100 (« au-delà, un lot en échec fait perdre
  beaucoup de travail ») ; `extend` explicitement documenté comme
  garant de l'ordre — exigence directe de l'utilisateur.
- Alternatives considered : taille de lot adaptative au nombre de
  tokens — rejeté en v1 (YAGNI ; la spec fixe une taille constante
  configurable).

## R-05 : Retry et erreurs transitoires

- Decision : retry exponentiel uniquement sur erreurs transitoires
  (timeout, erreur réseau, 429, 5xx) ; échec immédiat du document pour
  les 4xx hors 429. Délais : `--retry-time` initial (3 s par défaut),
  doublé à chaque essai, jusqu'à `--retry-occurences` essais (3 par
  défaut).
- Rationale : clarification session 2026-10-06 (Q2) ; 429/5xx sont
  récupérables côté serveur, 401/422/413 sont définitifs — retenter
  masque la cause et gaspille le budget retry.
- Alternatives considered : retry sur tout échec — rejeté ; aucun retry
  — rejeté (spécifié par l'utilisateur).

## R-06 : Format de l'état de reprise (checkpoint)

- Decision : un fichier JSON par document en cours sous
  `<output>/.checkpoints/<nom_d_input_sanitisé>.json`, contenant :
  modèle utilisé, taille de lot, vecteurs des lots déjà réussis (dans
  l'ordre). Supprimé dès que la matrice est écrite avec succès ;
  invalidé avec avertissement si le modèle change entre deux tentatives.
- Rationale : reprise au lot échoué sans rappeler l'API (FR-009,
  clarifications Q3/Q4) ; JSON lisible et débogable ; rangé sous le
  dossier de sortie = rétention contrôlée par l'utilisateur (Data
  Retention : l'utilisateur supprime le dossier, tout disparaît).
- Alternatives considered : `.npy` partiel + méta-JSON — rejeté en v1
  (deux fichiers, complexité inutile à l'échelle visée) ; checkpoints
  en mémoire — rejeté (reprise inter-exécutions exigée).

## R-07 : Compteur d'occurrence

- Decision : fichier texte `counter.txt` à la racine du projet,
  contenant uniquement le dernier numéro consommé (4 chiffres, ex.
  `0042`). Absent -> repart à 0001 ; illisible/corrompu -> échec rapide
  sans écrire de sortie. Cycle : 0001..9999, puis 0000, puis nouveau
  cycle. Persisté après chaque document produit, avant l'écriture de la
  matrice (un numéro consommé n'est jamais réutilisé).
- Rationale : FR-011 à FR-013 ; la persistance avant écriture garantit
  l'unicité même en cas d'interruption pendant la sauvegarde.
- Alternatives considered : compteur en SQLite — rejeté (YAGNI) ;
  horodatage — rejeté (la spec impose un cycle à 4 chiffres).

## R-08 : Nommage et écriture des sorties

- Decision : fichier `<18 premiers caractères du nom de fichier du
  JSON d'entrée (stem sanitisé, sans extension)>-<numéro à 4
  chiffres>.npy` (ex. `016472351681860015-0042.npy` pour
  `016472351681860015.json`). Corrigé le 2026-10-06 (bug
  titre-depuis-nom-json) : le nommage utilisait à tort le champ
  `document.title` et 20 caractères. La
  sanitisation neutralise uniquement les caractères interdits par le
  système de fichiers (`/ \ : * ? " < > |` et caractères de contrôle,
  remplacés par `_`) ; les espaces sont conservés. Matrice écrite en
  `float32` via `numpy.save` (dossier créé si absent).
- Rationale : FR-010 ; hypothèse de la spec (neutralisation) ; `float32`
  = moitié de l'espace disque, précision suffisante pour la similarité.
- Alternatives considered : `float64` — rejeté (double espace disque,
  aucun besoin exprimé) ; slug complet du titre — rejeté (troncature à
  20 imposée).

## R-09 : Parsing CLI

- Decision : `argparse` (stdlib) ; commande `vector INPUT...` avec les
  options `--choix-techno`, `--taille-batch`, `--retry-occurences`,
  `--retry-time`, `--output-folder` ; validation des bornes avec échec
  rapide et message explicite.
- Rationale : YAGNI (pas de `click`/`typer`) ; stdlib = zéro
  dépendance supplémentaire.
- Alternatives considered : `click` / `typer` — rejetés (dépendance
  sans bénéfice pour cinq options simples).

## R-10 : Validation du schéma JSON 1.0

- Decision : validation manuelle légère des champs requis :
  `schema_version == "1.0"`, `document.title` (chaîne non vide),
  `chunks` (liste non vide d'objets avec `ref` entier et `text` chaîne
  non vide) ; les autres champs (`length`, `boundary`, `part`, `page`,
  `position_in_part`, `atomic`, `params`) sont lus sans être
  interprétés. Messages d'erreur explicites avec le chemin d'input.
- Rationale : YAGNI — schéma simple et figé ; la doc d'entrée (schéma
  1.0) et les 4 exemples servent de référence.
- Alternatives considered : `pydantic` — rejeté en v1 (dépendance
  lourde pour un schéma figé).
