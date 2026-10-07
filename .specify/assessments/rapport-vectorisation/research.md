# Idea Research: Rapport JSON optionnel (`--rapport`)

- **Slug**: rapport-vectorisation
- **Created**: 2026-10-07
- **Evidence confidence (overall)**: medium

## Users & Demand

- Le dossier `output/` du projet contient déjà plusieurs matrices dont
  les noms ne diffèrent que par le stem tronqué et le numéro d'occurrence
  (ex. `016472351681860015-0002.npy`, `094056510632520017-0004.npy`) ;
  rien ne documente quel JSON d'entrée, quel modèle ou quelle dimension
  les a produites — [source: inspection de `output/` et de
  `src/vectorizator/output.py`] (confidence: high)
- Aucun utilisateur final identifié au-delà de l'auteur du projet
  (pipeline personnel Corsen AI / Vectorizator) ; la demande émane de
  l'utilisateur unique — [ASSUMPTION] (confidence: medium)
- Aucune demande, ticket ou spécification antérieure ne mentionne un
  rapport ou des métadonnées de sortie (grep
  `rapport|metadata|provenance|manifest` vide dans
  `specs/001-vectorisation-mistral-embed/`) — [source: recherche dans
  les specs existantes] (confidence: high)

## Prior Art

- **Interne** : le contrat CLI actuel
  (specs/001-vectorisation-mistral-embed/contracts/cli-contract.md)
  définit exactement 5 options (`--choix-techno`, `--taille-batch`,
  `--retry-occurences`, `--retry-time`, `--output-folder`) et une seule
  sortie par document : la matrice `.npy`. Aucune sortie secondaire
  n'existe ; le journal console (`[OK] source -> path`) est la seule
  trace, éphémère — [source: contracts/cli-contract.md,
  src/vectorizator/cli.py] (confidence: high)
- **Interne** : le bug `titre-depuis-nom-json` (.specify/bugs/) a déjà
  montré que la correspondance nom de sortie ↔ contenu d'entrée est
  fragile ; le nom de sortie ne code que 18 caractères du stem + un
  numéro d'occurrence global (counter.txt), pas le modèle ni la dimension
  — [source: src/vectorizator/output.py,
  .specify/bugs/titre-depuis-nom-json/] (confidence: high)
- **Externe** : le format `.npy` de NumPy stocke déjà shape et dtype dans
  son en-tête, reconstructibles sans charger les données
  (`numpy.lib.format`, `np.load(mmap_mode='r')`) — les champs
  « dimension » et « nature » du rapport proposé sont donc redondants
  avec l'en-tête du fichier lui-même, mais le champ « embed » (modèle
  utilisé) n'est stocké nulle part — [source: numpy.org/devdocs (extrait
  de recherche, page non consultée), stackoverflow.com (extrait de
  recherche, page non consultée)] (confidence: high)
- **Externe** : le motif « sidecar JSON à côté de l'artefact » est établi
  en ML/MLOps : `<file>.manifest.json` emportant kind, métadonnées,
  params et lineage (issue daanrongen/splat), `metadata.json` /
  `dataset_manifest.json` à côté des modèles (issue cctsao1008/fami-pixel),
  `provenance.json` par résultat (PR mlcommons/storage), métadonnées de
  provenance en JSON dans les pipelines MLflow/W3C PROV — [source:
  résultats de recherche web github.com (extraits, pages non consultées),
  sciencedirect.com (extrait, page non consultée)] (confidence: medium)

## Market & Context

- Alternative actuelle : ouvrir manuellement chaque `.npy` (np.load)
  pour lire shape/dtype, et deviner le modèle par recoupement avec
  l'historique console — impossible après coup, le modèle n'étant
  enregistré nulle part — [source: inspection du code,
  src/vectorizator/output.py] (confidence: high)
- Alternative externe lourde : un outil de suivi d'exécutions type
  MLflow pour capturer les métadonnées d'exécution — disproportionné pour
  un CLI local mono-utilisateur — [ASSUMPTION] (confidence: medium)
- Coût de l'inaction : les matrices accumulées dans `output/` deviennent
  progressivement non traçables (quel modèle, quelle dimension, quel
  JSON source), surtout avec le cycle du compteur 0001..9999 et des
  stems tronqués à 18 caractères — [source: counter.py, output.py]
  (confidence: medium)

## Data & Constraints

- Modèles supportés et dimensions fixes : `mistral-embed` (1024),
  `mistral-embed-dim256-2510` (256), `mistral-embed-dim128-2510` (128)
  — [source: src/vectorizator/config.py] (confidence: high)
- Le dtype de sortie est aujourd'hui toujours `float32` (cast dans
  `save_matrix`), ce qui rend le champ « nature » constant en l'état —
  [source: src/vectorizator/output.py:44] (confidence: high)
- Le nom de matrice est `<stem 18 car.>-<NNNN>.npy` ; un rapport « même
  nom en .json » coexisterait sans collision avec l'extension `.json`
  déjà exclue du stem — [source: src/vectorizator/output.py]
  (confidence: high)
- Constitution du projet : trafic réseau limité à l'API Mistral, clé API
  jamais écrite — le rapport JSON devra respecter la même contrainte (ne
  jamais contenir la clé ou des chemins sensibles) — [source:
  .specify/memory/constitution.md, contracts/cli-contract.md]
  (confidence: high)
- 85 fonctions de test existent (tests/), toutes hors réseau : une
  option `--rapport` devra rester testable sans réseau — [source:
  tests/] (confidence: high)

## Evidence Against the Idea

- Deux des cinq champs proposés (« dimension », « nature ») sont déjà
  lisibles dans l'en-tête du `.npy` lui-même, sans outil : le rapport
  duplique une information gratuite — [source: numpy.org (extrait de
  recherche, page non consultée)] (confidence: high)
- Le champ « nature » est constant (`float32`) tant que `save_matrix` ne
  change pas : faible valeur d'information — [source:
  src/vectorizator/output.py] (confidence: high)
- Un utilisateur unique et aucun signal de demande externe : le besoin de
  traçabilité est plausible mais non démontré — [ASSUMPTION]
  (confidence: medium)
- Un rapport par matrice (même nom que la matrice en `.json`) multiplie
  les fichiers dans `output/` et introduit une ambiguïté potentielle
  avec les JSON d'entrée (même extension) — [ASSUMPTION]
  (confidence: low)
- Le rapport ne dit rien du contenu des vecteurs (nombre de chunks,
  échecs par lot) : sa valeur dépend de ce que l'utilisateur veut en
  faire ensuite (aucun consommateur identifié à ce jour) — [ASSUMPTION]
  (confidence: medium)

## Gaps & Open Questions

- [NEEDS CLARIFICATION: un rapport par matrice `.npy` (sidecar, même
  nom) ou un rapport global unique pour toute l'exécution ?]
- [NEEDS CLARIFICATION: champ « entrée » — nom de fichier JSON brut
  (chemin complet ?) ou stem tronqué ?]
- [NEEDS CLARIFICATION: champ « embed » — identifiant du preset CLI
  (`mistral-embed`, etc.) ou nom du modèle API ?]
- [NEEDS CLARIFICATION: comportement si un document échoue — le rapport
  des documents réussis est-il quand même écrit ?]
- [NEEDS CLARIFICATION: le rapport inclut-il aussi des données déjà
  disponibles dans l'en-tête .npy (dimension, dtype) par commodité,
  malgré la redondance ?]
- [NEEDS CLARIFICATION: qui consomme ce rapport ensuite (l'utilisateur
  manuellement, un futur outil, un RAG en aval) ?]

## Sources

- `specs/001-vectorisation-mistral-embed/contracts/cli-contract.md`
  (contrat CLI actuel)
- `src/vectorizator/{cli,output,config}.py`, `tests/`, `output/`
  (inspection du code et des artefacts, lecture seule)
- numpy.org, `numpy.lib.format` (host: numpy.org, page non consultée —
  extrait de recherche web uniquement ; host hors liste d'hosts
  autorisés au fetch)
- stackoverflow.com/questions/64226337 (host: stackoverflow.com,
  allowlisted, extrait de recherche web uniquement — page non ouverte)
- github.com/daanrongen/splat/issues/132 (host: github.com, allowlisted,
  extrait de recherche web uniquement — page non ouverte)
- github.com/cctsao1008/fami-pixel/issues/34 (host: github.com,
  allowlisted, extrait de recherche web uniquement — page non ouverte)
- github.com/mlcommons/storage/pull/855 (host: github.com, allowlisted,
  extrait de recherche web uniquement — page non ouverte)
- sciencedirect.com/science/article/pii/S0306437924001534 (host:
  sciencedirect.com, non fetchable — extrait de recherche web
  uniquement, fetch non tenté)
