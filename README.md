# Vectorizator

Un outil CLI de vectorisation de JSON d'index (schéma 1.0) en matrices
NumPy via l'API Mistral Embeddings. Local-first : seuls les textes à
vectoriser sont envoyés à l'API Mistral ; tout le reste (sorties,
compteur, état de reprise) reste sur votre machine.

## Installation

```bash
pip install -e .
```

## Configuration

Copier `.env.example` en `.env` à la racine du projet et renseigner la
clé (jamais committée, le fichier est gitignoré) :

```text
MISTRAL_API_KEY=YOUR_API_KEY
```

## Utilisation

```bash
vector Examples/mon_index.json [options]
vector Examples/            # dossier : tous les .json, tri alphabétique
```

Options :

| Option | Défaut | Bornes / valeurs |
| -------- | -------- | ------------------ |
| `--choix-techno` | `mistral-embed` | voir valeurs ci-dessous |
| `--taille-batch` | 25 | 0 à 100 ; 0 = pas de batch |
| `--retry-occurences` | 3 | 0 à 10 |
| `--retry-time` | 3 | 1 à 10 (secondes) |
| `--output-folder` | `output` | créé si absent |

Valeurs acceptées pour `--choix-techno` :

- `mistral-embed` (1024 dimensions, défaut)
- `mistral-embed-dim256-2510` (256 dimensions)
- `mistral-embed-dim128-2510` (128 dimensions)

Sorties : une matrice `.npy` par JSON traité, dans le dossier de
sortie, nommée `<18 premiers caractères du nom de fichier du JSON,
sans extension>-<NNNN>.npy` — une ligne par chunk, dans l'ordre exact
du JSON d'entrée.

Robustesse : requêtes par lots (25 chunks par défaut), retry
exponentiel sur les erreurs transitoires (429, 5xx, réseau), reprise au
lot échoué sans recalcul (checkpoints sous `output/.checkpoints/`,
supprimés après succès).

Le compteur d'occurrence `counter.txt` vit à la racine du projet : un
numéro consommé n'est jamais réutilisé, même en cas d'interruption.

## Tests

```bash
pytest
```

Aucun appel réseau pendant les tests : le client SDK est simulé.
