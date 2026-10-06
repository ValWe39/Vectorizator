# Data Model: Vectorisation JSON via Mistral Embed

Session 2026-10-06 — Phase 1. Entités, champs, règles de validation et
transitions d'état, dérivés de la spec et de research.md.

## 1. JSON d'index (input)

Fichier au schéma 1.0 ; unité d'entrée du processus, traité
indépendamment des autres (N inputs = N sorties).

- `schema_version` : chaîne, DOIT valoir `"1.0"`.
- `document` : objet ; `title` : chaîne non vide (source du nom de
  sortie) ; `path`, `structure`, `typologie` : lus sans interprétation.
- `params` : objet (`chunk_min`, `chunk_max`, `overlap_pct`,
  `guillemets`, `unit`) : lus sans interprétation.
- `chunks` : liste non vide d'entités Chunk (voir §2) ; l'ordre de la
  liste fixe l'ordre des lignes de la matrice.

Validation : tout écart -> échec rapide avec message explicite pour ce
seul fichier ; les autres inputs continuent (sauf compteur corrompu :
échec global).

## 2. Chunk

Fragment de texte d'un document source ; appartient à un JSON d'index.

- `ref` : entier, rang séquentiel (1, 2, 3...).
- `text` : chaîne non vide — seul champ vectorisé.
- `length` : entier (lu) ; `boundary` : chaîne (lu) ; `part` : chaîne
  (lue) ; `page` : entier optionnel (lu) ; `position_in_part` : entier
  (lu) ; `atomic` : booléen (lu, jamais utilisé pour fusionner).

Relation : 1 JSON d'index contient N chunks, ordre significatif.

## 3. Preset de modèle d'embedding

Association nom de modèle API / dimension de sortie.

| Nom de modèle | Dimensions | Défaut |
|---------------|------------|--------|
| `mistral-embed` | 1024 | oui |
| `mistral-embed-dim256-2510` | 256 | non |
| `mistral-embed-dim128-2510` | 128 | non |

Validation : `--choix-techno` DOIT être l'un des trois noms exacts.
Relation : détermine la largeur de la matrice et le nom passé à l'API.

## 4. Lot (batch)

Groupe de chunks envoyés en une seule requête API.

- `index_debut`, `index_fin` : bornes dans la liste des chunks.
- `textes` : liste des `text` des chunks couverts.
- `statut` : `en_cours` | `reussi` | `echec`.

Transitions : `en_cours` -> `reussi` (réponse API valide) ; `en_cours`
-> `echec` (erreurs transitoires épuisées ou erreur définitive 4xx hors
429). Un lot `echec` reste reprisable tant que le checkpoint existe.

Découpe : lots de `--taille-batch` chunks (25 par défaut, 0-100) ;
`0` = un lot d'un chunk (requête simple, pas de regroupement).

## 5. Matrice de sortie

Fichier `.npy` produit par document traité avec succès.

- `shape` : `(n_chunks, dimension_du_modele)` — ligne i <-> chunk i,
  ordre strict (assemblage par `extend`).
- `dtype` : `float32`.
- `nom` : `<20 premiers caractères du titre sanitisé>-<NNNN>.npy`.
- `emplacement` : dossier de sortie (`output` par défaut, créé si
  absent ; `--output-folder` pour un chemin alternatif).

Relation : 1:1 avec un traitement de document réussi ; le numéro
d'occurrence la rend unique au sein des exécutions.

## 6. Compteur d'occurrence

- Fichier : `counter.txt` à la racine du projet.
- Contenu : uniquement le dernier numéro consommé, 4 chiffres
  (ex. `0042`), sans autre donnée.
- Valeurs : 0000..9999 ; cycle 0001..9999 -> 0000 -> 0001.
- Absent -> premier usage à 0001. Illisible/corrompu -> échec rapide
  global, aucune sortie écrite.

Transitions : `absent` -> `0001` ; `n` -> `n+1` (n < 9999) ; `9999` ->
`0000` ; `0000` -> `0001`. Persisté après chaque document produit, avant
l'écriture de la matrice — un numéro consommé n'est jamais réutilisé,
même en cas d'interruption.

## 7. État de reprise (checkpoint)

Fichier JSON par document en cours : `<output>/.checkpoints/<nom
d'input sanitisé>.json`.

- `model` : nom du modèle utilisé (clé d'invalidation).
- `batch_size` : taille de lot utilisée.
- `vectors` : liste des vecteurs des lots déjà réussis, dans l'ordre.

Transitions : créé au premier lot réussi ; enrichi à chaque lot
réussi ; supprimé dès que la matrice est écrite ; invalidé (avec
avertissement, re-vectorisation depuis le premier lot) si `model`
change entre deux tentatives.

## 8. Clé API

- Source : variable d'environnement `MISTRAL_API_KEY` (chargée depuis
  le `.env` gitignoré).
- Usage : uniquement les appels d'embedding Mistral.
- Interdits : copie, écriture, affichage, log — nulle part.
- Absente/vide -> échec rapide avant tout appel réseau.

## Cycle de vie d'un traitement de document

```text
EN_ATTENTE -> EN_COURS (lots successifs, retry si transitoire)
EN_COURS -> ECHEC (lot echoue : checkpoint conserve, document saute)
ECHEC -> EN_COURS (relance : reprise au lot echoue, si meme modele)
EN_COURS (tous lots reussis) -> numero attribue + compteur persiste
        -> matrice .npy ecrite -> checkpoint supprime -> SUCCES
```
