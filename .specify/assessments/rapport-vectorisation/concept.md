# Concept: Trace de traçabilité optionnelle

- **Slug**: rapport-vectorisation
- **Created**: 2026-10-07
- **Recommended option**: Option B — Sidecar JSON par matrice, activé par
  `--rapport`

## Options

### Option A — Ne rien construire (statu quo amélioré par l'existant)

- **Sketch**: aucun changement du CLI. Qui veut traîner une matrice ouvre
  son en-tête `.npy` (dimension, dtype) avec `np.load` et recoupe avec
  l'historique console de son exécution. La traçabilité du modèle et du
  document source reste impossible après coup.
- **Appetite**: small (nul — rien à construire)
- **Trade-offs**: gagne zéro coût et zéro maintenance ; sacrifie
  l'objectif central du problème (le modèle utilisé n'est enregistré
  nulle part, la perte est irréversible). Le coût de re-vectorisation en
  cas de doute paie très vite plus cher que n'importe quelle option.
- **Rabbit holes**: aucun — mais l'écart avec la métrique de succès
  (« vérifiable sans ouvrir la matrice ») est total.

### Option B — Sidecar JSON par matrice, activé par `--rapport`

(le plus petit qui marche)

- **Sketch**: une option booléenne `--rapport`, désactivée par défaut.
  Quand elle est activée, chaque matrice `.npy` écrite avec succès est
  accompagnée d'un fichier JSON portant le même nom (extension `.json`),
  décrivant le document d'entrée, la matrice produite, le modèle
  d'embedding, la dimension et le dtype. L'utilisateur lit ce fichier à
  la main ou depuis un script en aval ; il voyage avec la matrice si elle
  est déplacée.
- **Appetite**: small (quelques jours : une option CLI, une écriture
  JSON, des tests hors réseau)
- **Trade-offs**: gagne la traçabilité complète au niveau le plus utile
  (la matrice), en opt-in strict sans changement de comportement par
  défaut, avec le motif sidecar éprouvé en ML (research.md, Prior Art).
  Sacrifie : une redondance partielle avec l'en-tête `.npy` (dimension,
  dtype — redondance choisie par commodité de lecture), un risque de
  confusion visuelle entre sidecars `.json` et JSON d'entrée dans un même
  dossier si l'utilisateur place les deux au même endroit, et le
  doublement du nombre de fichiers dans `output/` quand l'option est
  active.
- **Rabbit holes**: enrichissement indéfini du rapport (nombre de
  chunks, erreurs par lot, durées, coûts, horodatage, versions de
  schéma) — tenu hors périmètre par les non-goals du problem.md ;
  gestion de documents en échec (rapport partiel ? entrée « échoué » ?)
  — à trancher en spécification, pas ici.

### Option C — Manifest global d'exécution (append)

- **Sketch**: au lieu d'un fichier par matrice, `--rapport` alimente un
  manifest unique dans le dossier de sortie (une ligne par document
  traité, cumulé entre exécutions), façon registre de provenance
  MLflow-lite local.
- **Appetite**: medium (multi-jours à semaines : format de manifest,
  concurrence entre exécutions, rotation, nettoyage, plus de surface de
  test)
- **Trade-offs**: gagne une vue d'ensemble du parc de matrices et évite
  la multiplication des fichiers ; sacrifie la propriété la plus
  précieuse du sidecar — le voyage avec la matrice déplacée — et
  introduit des questions propres (écrasement, croissance illimitée,
  cohérence avec les suppressions manuelles de `.npy`).
- **Rabbit holes**: format de manifest versionné, migration des entrées,
  collisions d'exécutions concurrentes — toutes des dépenses que rien
  dans la recherche ne justifie pour un CLI mono-utilisateur.

## Recommendation

**Option B.** C'est la seule qui satisfait les trois buts du problem.md
simultanément : traçabilité durable par matrice, comportement par défaut
strictement inchangé (métrique « sorties identiques sans l'option »),
et conformité aux contraintes du projet (aucun réseau, pas de secret,
testable hors ligne). Son appetite (small) est à la mesure du signal de
demande — réel mais émanant de l'unique opérateur du projet. L'Option A
laisse le coût de l'inaction s'accumuler (perte irréversible,
re-vectorisation payante) ; l'Option C dépense un appetite medium pour
un bénéfice (vue globale) qu'aucune preuve ne demande. La redondance
dimension/dtype avec l'en-tête `.npy` est assumée : elle rend le rapport
lisible sans outil, ce qui est la métrique de succès.

## Out of Scope (for the recommended option)

- Tout ce que la matrice `.npy` ne demande pas : nombre de chunks,
  échecs par lot, durées, coûts API, horodatage, version du schéma du
  rapport (non-goals hérités du problem.md).
- Manifest global d'exécution (Option C rejetée).
- Rétro-documentation des matrices déjà présentes dans `output/`.
- Modification du nommage ou du format des matrices.
- Tout changement de comportement sans l'option `--rapport` (sorties,
  codes de sortie, console).

## Assumptions to Validate

- La granularité par matrice (sidecar) est bien celle voulue par
  l'utilisateur — l'intake le suggère (« même titre que la matrice en
  .json ») mais l'option C n'a jamais été explicitement écartée par lui.
- Le consommateur du rapport est une lecture humaine ou un script
  simple : un JSON plat à cinq champs suffit ; pas de besoin de schéma
  versionné.
- Les cinq champs de l'intake (entrée, sortie, embed, dimension,
  nature) sont le contenu voulu, sans horodatage ni métadonnée
  d'exécution.
- Le rapport n'est écrit que pour les documents réussis ; les échecs
  restent signalés en console comme aujourd'hui.
- Le champ « entrée » désigne le nom de fichier du JSON d'entrée (pas
  son chemin absolu, pour ne pas fuir d'information sur la machine).
