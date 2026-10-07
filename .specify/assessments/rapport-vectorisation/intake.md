# Idea Intake: Rapport JSON optionnel (`--rapport`)

- **Slug**: rapport-vectorisation
- **Created**: 2026-10-07
- **Source**: pasted text
- **Type**: improvement

## Idea (as captured)

> J'envisage d'ajouter en sortie, sous commande optionnelle "--rapport",
> non activée par défaut, un json présentant les éléments suivants à chaque
> fichier requêté :
>
> - "entrée" : titre du document d'entrée "XXXXXXXXXX.json"
> - "sortie" : titre de la matrice de sortie "XXXXXXXXXX-XXXX.npy"
> - "embed" : Type d'embeding utilisé
> - "dimension" : dimension des vecteurs (1024, etc.)
> - "nature" : nature des float des vecteurs (float32, 64, etc. )
>
> Le titre de ce rapport serait le même que la matrice npy mais en .json

## Restated

Ajouter au CLI `vector` une commande optionnelle `--rapport`, désactivée
par défaut, qui produit en sortie un fichier JSON décrivant, pour chaque
fichier requêté, le document d'entrée, la matrice `.npy` produite, le type
d'embedding, la dimension des vecteurs et la nature des floats. Ce
rapport porterait le même nom que la matrice de sortie, avec l'extension
`.json`.

## Origin & Context

- **Raised by**: l'utilisateur (projet Vectorizator, branche 002-Noyau)
- **Trigger**: réflexion sur la traçabilité des sorties de vectorisation
  après l'implémentation de l'outil `vector` (commit 62b45d0)

## First-Glance Unknowns

- [NEEDS CLARIFICATION: un rapport par matrice `.npy` ou un rapport global
  pour l'ensemble des fichiers requêtés ?]
- [NEEDS CLARIFICATION: champ "entrée" — nom de fichier brut ou le titre
  issu des 18 premiers caractères du nom JSON (règle actuelle de nommage
  des sorties) ?]
- [NEEDS CLARIFICATION: champ "embed" — désigne le nom du modèle (ex.
  Mistral Embed) ou un identifiant de type d'embedding ?]
- [NEEDS CLARIFICATION: le rapport est-il écrit à côté de la matrice dans
  le même répertoire de sortie, ou ailleurs ?]
- [NEEDS CLARIFICATION: comportement attendu si un même lot produit
  plusieurs matrices (batching, reprise par checkpoint) — un rapport par
  checkpoint ?]
