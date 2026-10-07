# Decision: Trace de traçabilité optionnelle

- **Slug**: rapport-vectorisation
- **Decided**: 2026-10-07
- **Verdict**: go
- **Artifacts reviewed**: intake.md | research.md | problem.md |
  concept.md

## Scorecard

| Criterion | Rating | Justification |
|-----------|--------|---------------|
| Problem validity | adequate | Problème interne réel, audience de un |
| Evidence strength | adequate | Faits internes solides, demande moyenne |
| Value vs. inaction | strong | Perte irréversible ; recours payant |
| Feasibility / appetite | strong | Option B : small, opt-in, hors réseau |
| Strategic fit | strong | Constitution : sans réseau, sans secret |
| Risk posture | adequate | Risques identifiés ; granularité tranchée |

## Verdict & Rationale

**Go.** Le problème est réel et observé sur le parc de matrices
existant, le coût de l'inaction est supérieur au coût de l'option la
plus légère, et l'option B tient dans un appetite small tout en
respectant strictement le comportement par défaut (métrique de succès
n°2). L'evidence strength est « adequate » et non « strong » : la
demande émane d'un seul opérateur et le prior art externe repose sur
des extraits — c'est précisément pourquoi la solution recommandée est
la plus petite qui marche, pas un manifest global. La sélection
explicite de l'option B par l'utilisateur lève l'hypothèse la plus
risquée du concept (granularité sidecar vs manifest).

## If go — Handoff to `/speckit-specify`

- **Problem**: l'utilisateur du CLI `vector` ne peut pas, après coup,
  déterminer quel JSON d'entrée, quel modèle et quelle dimension ont
  produit une matrice `.npy` donnée ; la seule trace est console et
  éphémère, la perte est irréversible.
- **Chosen approach**: Option B — sidecar JSON par matrice, activé par
  une option booléenne `--rapport` désactivée par défaut ; rapport
  portant le même nom que la matrice (extension `.json`), avec cinq
  champs : entrée (document JSON source), sortie (matrice `.npy`),
  embed (modèle), dimension, nature (dtype).
- **In scope**: opt-in strict sans l'option (`--rapport` désactivée par
  défaut) ; rapport écrit pour chaque matrice produite avec succès ;
  cinq champs de l'intake ; écriture à côté de la matrice dans le
  dossier de sortie.
- **Out of scope**: traçage du contenu des vecteurs (chunks, échecs par
  lot, durées, coûts, horodatage, version de schéma) ; manifest global
  d'exécution ; rétro-documentation des matrices existantes ;
  modification du nommage ou du format des `.npy` ; tout changement de
  comportement sans l'option.
- **Success metrics**:
  - correspondance matrice → (source, modèle, dimension) vérifiable sans
    ouvrir la matrice ni console ;
  - sorties et codes de sortie identiques à aujourd'hui sans l'option
    (suite de tests existante, 85 fonctions) ;
  - exactement 1 fichier `.npy` par JSON réussi par défaut, + 1 `.json`
    sidecar quand l'option est active.
- **Carried-forward open questions**:
  - [NEEDS CLARIFICATION: contenu exact du champ « entrée » — nom de
    fichier du JSON seul (recommandé : pas de chemin absolu, pas de
    fuite d'information machine) ou chemin complet ?]
  - [NEEDS CLARIFICATION: champ « embed » — identifiant du preset CLI
    (`mistral-embed`, `mistral-embed-dim256-2510`,
    `mistral-embed-dim128-2510`) ; à figer en spécification]
  - [NEEDS CLARIFICATION: gestion des collisions visuelles sidecar
    `.json` / JSON d'entrée si l'utilisateur pointe `--output-folder`
    vers le dossier des sources ; à trancher en spécification
    (interdire, avertir, ou ignorer)]
  - [NEEDS CLARIFICATION: comportement quand le rapport existe déjà
    (re-vectorisation du même document avec nouveau numéro d'occurrence
    → nouveau nom, donc pas de collision attendue ; à confirmer en
    spécification)]
