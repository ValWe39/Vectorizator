# Contrat CLI : `vector`

Schéma de commandes de Vectorizator (interface utilisateur unique de
l'outil). Référence : spec.md (FR-001 à FR-017), data-model.md.

## Usage

```text
vector INPUT [INPUT...] [OPTIONS]
```

- `INPUT` : un ou plusieurs chemins (fichiers `.json` ou dossiers).
- Détection automatique : un fichier, plusieurs fichiers ou un dossier
  sont acceptés sans option dédiée (FR-001).
- Dossier : seuls les fichiers `.json` sont traités, dans l'ordre
  alphabétique ; les autres fichiers sont ignorés sans erreur.
- Chaque JSON est traité indépendamment : N inputs = N sorties.

## Options

| Option | Type | Défaut | Bornes / valeurs |
|--------|------|--------|------------------|
| `--choix-techno` | nom | `mistral-embed` | voir valeurs ci-dessous |
| `--taille-batch` | int | 25 | 0 à 100 ; 0 = pas de batch |
| `--retry-occurences` | int | 3 | 0 à 10 |
| `--retry-time` | int (s) | 3 | 1 à 10 |
| `--output-folder` | chemin | `output` | créé si absent |

Valeurs acceptées pour `--choix-techno` :

- `mistral-embed` (1024 dimensions, défaut)
- `mistral-embed-dim256-2510` (256 dimensions)
- `mistral-embed-dim128-2510` (128 dimensions)

Toute valeur hors bornes -> échec rapide avec message explicite, avant
tout appel API et sans consommer de numéro d'occurrence (FR-016).

## Sorties

- Un fichier `<stem du nom de fichier, 18 car.>-<NNNN>.npy` par JSON
  traité avec succès (extension `.json` exclue),
  dans le dossier de sortie ; matrice de shape
  `(n_chunks, dimension du modèle)`, une ligne par chunk dans l'ordre
  du JSON.
- Le numéro `NNNN` provient du compteur persistant `counter.txt`
  (racine du projet) ; consommé et persisté à chaque document produit,
  jamais réutilisé ; cycle 0001..9999 -> 0000 -> 0001.

## Environnement

- `MISTRAL_API_KEY` : requise (chargée depuis `.env` ou l'environnement).
  Absente ou vide -> échec rapide avant tout appel réseau.
- Seul trafic sortant autorisé : l'endpoint Mistral `/v1/embeddings`.

## Comportement d'erreur

- Erreur définitive (4xx hors 429, JSON invalide, clé absente, option
  hors bornes, compteur corrompu) -> échec immédiat du document
  concerné avec message explicite ; en multi-input, les autres inputs
  continuent (sauf compteur corrompu : arrêt global).
- Erreur transitoire (timeout, réseau, 429, 5xx) -> retry exponentiel :
  premier essai après `--retry-time` secondes, délai doublé à chaque
  essai, jusqu'à `--retry-occurences` essais ; au-delà, état de
  reprise conservé pour reprendre au lot échoué.

## Codes de sortie

| Code | Signification |
|------|---------------|
| 0 | Tous les inputs traités avec succès |
| 1 | Erreur de configuration ou de validation (avant traitement) |
| 2 | Au moins un document en échec (les autres peuvent avoir réussi) |

## Journal console

- Progression par document et par lot (indice du lot / total).
- Avertissements : invalidation de checkpoint (changement de modèle),
  fichiers ignorés dans un dossier, reprises effectuées.
- La clé API n'apparaît jamais dans les messages.
