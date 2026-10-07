# Quickstart : valider l'option `--rapport`

Guide de validation exécutable de bout en bout. Références :
contracts/cli-contract.md (amendement du schéma de commandes),
data-model.md (entité Rapport de traçabilité), quickstart de la
feature 001 pour le socle (`specs/001-vectorisation-mistral-embed/
quickstart.md`).

## Prérequis

- Python 3.11+ ; installation : `pip install -e .` (dépôt racine).
- Clé `MISTRAL_API_KEY` dans un fichier `.env` à la racine du projet
  (gitignoré — jamais committé) pour les scénarios réseau.
- Un JSON de `Examples/` comme corpus de test.

## Scénario 1 : rapport nominal

```bash
vector Examples/016472351681860015.json --rapport
```

Attendu : exit 0 ; dans `output/`, deux fichiers de même nom —
`016472351681860015-NNNN.npy` et `016472351681860015-NNNN.json` (même
numéro d'occurrence). Le JSON contient exactement cinq clés —
`entrée` = `016472351681860015.json`, `sortie` =
`016472351681860015-NNNN.npy`, `embed` = `mistral-embed`,
`dimension` = 1024, `nature` = `float32` — et aucun chemin absolu ni
clé.

## Scénario 2 : défaut inchangé

```bash
vector Examples/016492360000000016.json
```

Attendu : exit 0 ; exactement un fichier `.npy` créé, aucun fichier
`.json` de rapport, mêmes messages console et code de sortie que le
comportement antérieur à la feature.

## Scénario 3 : cohérence des champs avec le modèle

```bash
vector Examples/094056510632520017.json --rapport --choix-techno mistral-embed-dim256-2510
```

Attendu : exit 0 ; le rapport indique `embed` =
`mistral-embed-dim256-2510` et `dimension` = 256 ; la matrice a 256
colonnes ; `nature` = `float32`.

## Scénario 4 : multi-input avec échec partiel

1. Créer un dossier temporaire contenant un JSON valide de `Examples/`
   et un fichier `.json` invalide (par ex. `{}`).
2. Lancer `vector <dossier_temporaire> --rapport`.

Attendu : exit 2 ; un rapport et une matrice pour le JSON valide,
rien pour l'invalide ; message d'erreur explicite pour l'invalide ;
les numéros d'occurrence des rapports correspondent à leurs matrices.

## Scénario 5 : re-vectorisation

```bash
vector Examples/016472351681860015.json --rapport
vector Examples/016472351681860015.json --rapport
```

Attendu : deux paires matrice/rapport distinctes avec des numéros
d'occurrence consécutifs (le compteur n'est jamais réutilisé) ; la
première paire n'est ni modifiée ni supprimée.

## Scénario 6 : tests automatisés

```bash
pytest
```

Attendu : tests verts, y compris les nouveaux tests du rapport
(nommage, contenu des cinq champs, défaut sans l'option, échec
d'écriture) — aucun appel réseau réel pendant `pytest` (client SDK
simulé).
