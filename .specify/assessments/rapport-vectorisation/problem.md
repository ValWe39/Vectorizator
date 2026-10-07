# Problem Definition: Traçabilité des matrices de vectorisation produites

- **Slug**: rapport-vectorisation
- **Created**: 2026-10-07
- **Inputs used**: intake.md | research.md

## Problem Statement

L'utilisateur du CLI `vector` ne peut pas, après coup, déterminer quel
JSON d'entrée, quel modèle d'embedding et quelle dimension ont produit
une matrice `.npy` donnée dans le dossier de sortie : le seul
enregistrement de la correspondance est un message console éphémère, et
le nom de sortie ne code que 18 caractères du stem et un numéro
d'occurrence. À mesure que les matrices s'accumulent (et que le compteur
cycle), le dossier `output/` devient progressivement inexploitable sans
deviner ou re-vectoriser.

## Affected Users & Stakeholders

- **Users**: l'opérateur du CLI `vector` (l'auteur du projet, pipeline
  Corsen AI / Vectorizator) — au moment de réutiliser, comparer ou auditer
  des matrices existantes, il ne sait plus à quel document source et à
  quel modèle elles se rapportent — [source: research.md, inspection de
  `output/`]
- **Stakeholders**: le propriétaire du projet (même personne) — décide si
  la traçabilité vaut l'ajout d'une sortie supplémentaire et de sa
  maintenance (contrat CLI, tests) — [NEEDS CLARIFICATION: existence
  d'autres consommateurs en aval des matrices (outil RAG, futur script)
  à confirmer]

## Goals

- Pouvoir retrouver, pour toute matrice `.npy` produite, le document JSON
  d'entrée, le modèle d'embedding et la dimension utilisés — de manière
  durable (persistée dans un fichier), pas seulement dans la console.
- Conserver le comportement actuel inchangé par défaut : aucune sortie
  supplémentaire ni changement de sortie pour qui ne demande pas la
  traçabilité.
- Rester dans les contraintes du projet : pas de réseau supplémentaire,
  jamais de clé API ni de donnée sensible dans la trace, testable hors
  ligne.

## Non-Goals

- Tracer le contenu des vecteurs (nombre de chunks, échecs par lot,
  durée, coûts API) — la recherche n'a montré aucune demande pour cela.
- Un système de suivi d'expériences type MLflow ou une base de
  métadonnées — disproportionné pour un CLI local mono-utilisateur
  (research.md, Market & Context).
- Modifier le nommage ou le format des matrices `.npy` existantes.
- Rétro-documenter les matrices déjà présentes dans `output/` — leur
  provenance est définitivement perdue.

## Success Metrics

- Pour un lot de N JSON traités avec la trace activée, la correspondance
  matrice → (document source, modèle, dimension) est vérifiable sans
  ouvrir la matrice et sans console (qualitatif ; baseline actuelle :
  impossible).
- Sans l'option activée, les sorties et le code de sortie du CLI sont
  identiques à aujourd'hui (baseline : comportement du commit 6c24336 ;
  vérifiable par la suite de tests existante, 85 fonctions de test).
- Aucune régression du nombre de fichiers produits par défaut
  (baseline : exactement 1 fichier `.npy` par JSON réussi).

## Cost of Inaction

Chaque nouvelle exécution ajoute des matrices non traçables au dossier
`output/`. Le modèle utilisé n'étant enregistré nulle part, un changement
de `--choix-techno` (1024, 256 ou 128 dimensions) rend impossible de
distinguer a posteriori des matrices issues de modèles différents
portant des stems voisins ; le seul recours est de re-vectoriser les
documents, au coût des appels API correspondants. La perte est
irréversible pour les matrices déjà écrites.

## Open Questions

- [NEEDS CLARIFICATION: qui consomme la trace — lecture humaine
  ponctuelle, ou futur outil/script en aval (ce qui conditionne le format
  et la granularité) ?]
- [NEEDS CLARIFICATION: granularité de la trace — par matrice (sidecar
  voyageant avec le `.npy`) ou par exécution (un fichier pour tout le
  lot) ? La recherche montre les deux motifs existants en prior art ;
  l'intake penche pour le sidecar (« même titre que la matrice en
  .json ») mais sans certitude sur le multi-input]
- [NEEDS CLARIFICATION: comportement attendu quand certains documents du
  lot échouent — la trace des réussites doit-elle exister ?]
- [NEEDS CLARIFICATION: les champs redondants avec l'en-tête `.npy`
  (dimension, dtype) doivent-ils figurer dans la trace par commodité, ou
  la trace se limite-t-elle à l'information absente (document source,
  modèle) ?]
