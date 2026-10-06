# Quickstart : valider Vectorizator

Guide de validation exécutable de bout en bout. Références :
contracts/cli-contract.md (schéma de commandes), data-model.md (entités).

## Prérequis

- Python 3.11+ ; installation : `pip install -e .` (dépôt racine).
- Clé `MISTRAL_API_KEY` dans un fichier `.env` à la racine du projet
  (gitignoré — jamais committé).
- Les 4 JSON de `Examples/` comme corpus de test.

## Scénario 1 : cas nominal (un JSON)

```bash
vector Examples/016472351681860015.json
```

Attendu : exit 0 ; un fichier `output/<stem du nom de fichier,
18 car.>-NNNN.npy` créé (ex. `016472351681860015-0001.npy`),
chargeable avec `numpy.load`, de shape `(n_chunks, 1024)` —
n_chunks = nombre de chunks du JSON d'entrée ; ordre des lignes =
ordre des chunks.

## Scénario 2 : multi-input (dossier)

```bash
vector Examples/
```

Attendu : exit 0 ; 4 matrices créées dans `output/` (une par JSON),
numéros d'occurrence consécutifs sans doublon ; les fichiers non-JSON du
dossier (s'il y en a) ignorés avec avertissement.

## Scénario 3 : choix de modèle

```bash
vector Examples/016492360000000016.json --choix-techno mistral-embed-dim256-2510
```

Attendu : matrice de shape `(n_chunks, 256)`. Idem avec
`mistral-embed-dim128-2510` -> 128 colonnes ; sans option -> 1024.

## Scénario 4 : sans batch

```bash
vector Examples/094056510632520017.json --taille-batch 0
```

Attendu : exit 0 ; les logs montrent des requêtes simples (une par
chunk), pas de regroupement ; matrice identique en shape et ordre.

## Scénario 5 : reprise après échec réseau

1. Lancer `vector Examples/<json>` puis couper le réseau pendant le
   traitement (ou simuler une erreur transitoire).
2. Attendu : retries exponentiels visibles (3 s, 6 s, 12 s par défaut),
   puis échec du document avec exit 2 ; checkpoint présent sous
   `output/.checkpoints/`.
3. Rétablir le réseau et relancer la même commande.
4. Attendu : la reprise repart du lot échoué (les lots déjà réussis ne
   sont pas renvoyés — visible dans les logs) ; matrice produite ;
   checkpoint supprimé après succès.

## Scénario 6 : compteur d'occurrence

```bash
vector Examples/094056512116970018.json
vector Examples/094056512116970018.json
```

Attendu : deux exécutions -> deux numéros consécutifs (`counter.txt`
à la racine contient uniquement le dernier, ex. `0042`), deux fichiers
distincts ; relancer un JSON déjà réussi produit un nouveau document
avec un nouveau numéro (pas de détection de doublon).

## Scénario 7 : erreurs (fail-fast)

- Sans `MISTRAL_API_KEY` -> échec rapide, message explicite, aucun
  appel réseau, aucune sortie.
- `--taille-batch 150` -> erreur de bornes avant tout traitement.
- Fichier JSON invalide -> message explicite pour ce fichier ; en
  multi-input, les autres inputs sont traités.
- `counter.txt` corrompu (contenu non numérique) -> arrêt global
  immédiat, aucune sortie écrite.

## Scénario 8 : tests automatisés

```bash
pytest
```

Attendu : tests unitaires verts (compteur, checkpoints, validation de
schéma, nommage, retry) et tests d'intégration du pipeline avec client
SDK simulé — aucun appel réseau réel pendant `pytest`.
