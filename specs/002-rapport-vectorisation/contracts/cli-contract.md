# Contrat CLI : `vector` — amendement `--rapport` (feature 002)

Amendement du contrat de la feature 001
(`specs/001-vectorisation-mistral-embed/contracts/cli-contract.md`),
inchangé pour tout le reste : usage, options, sorties, codes de sortie,
journal console. Référence : spec.md (FR-001 à FR-012), data-model.md.

## Options (amendement)

L'option suivante s'ajoute aux cinq options existantes :

| Option | Type | Défaut | Bornes / valeurs |
| -------- | ------ | -------- | ------------------ |
| `--rapport` | flag | inactif | présent = actif |

`--rapport` est un flag booléen : présent sur la ligne de commande =
actif, absent = inactif. Aucune valeur, aucune borne. La validation des
autres options (FR-012 de la spec 002) est inchangée ; `--rapport` ne
consomme pas de numéro d'occurrence et ne déclenche rien avant le
traitement.

## Sorties (amendement)

- Sans `--rapport` : inchangé — exactement un fichier `.npy` par JSON
  traité avec succès, aucun fichier supplémentaire, messages console et
  codes de sortie identiques (FR-002).
- Avec `--rapport` : en plus de chaque matrice `.npy` écrite avec
  succès, un rapport JSON portant exactement le même nom que la
  matrice, extension `.json` (ex. `016472351681860015-0042.json` pour
  `016472351681860015-0042.npy`), dans le même dossier de sortie.

Contenu du rapport (objet JSON plat, UTF-8, indenté, cinq clés — cf.
data-model.md §1) :

```json
{
  "entrée": "016472351681860015.json",
  "sortie": "016472351681860015-0042.npy",
  "embed": "mistral-embed",
  "dimension": 1024,
  "nature": "float32"
}
```

- `entrée` : nom du fichier JSON d'entrée seul — jamais de chemin
  absolu, jamais de clé API (FR-005, FR-009).
- `sortie` : nom du fichier matrice avec extension.
- `embed` : identifiant exact du modèle (`--choix-techno`).
- `dimension` : entier — dimension du modèle (1024 / 256 / 128).
- `nature` : nom du dtype des flottants de la matrice (`float32`).

## Comportement d'erreur (amendement)

- Un document en échec ne produit ni matrice ni rapport ; les autres
  documents du lot continuent et reçoivent leurs rapports (FR-008).
- Erreur locale d'écriture du rapport alors que la matrice est écrite
  (disque plein, droits insuffisants) : le document est compté en
  échec avec message explicite, la matrice est conservée, le lot
  continue ; pas de retry (FR-011).
- Écriture du rapport : aucun appel réseau, aucune nouvelle dépendance
  (FR-010) ; testable hors ligne.

## Codes de sortie (inchangé)

| Code | Signification |
| ------ | --------------- |
| 0 | Tous les inputs traités avec succès |
| 1 | Erreur de configuration ou de validation |
| 2 | Au moins un document en échec (les autres peuvent avoir réussi) |

Un échec d'écriture du rapport compte comme échec documentaire
(code 2) ; un échec de validation avec `--rapport` présent reste un code
1 avant tout traitement, comme les autres options.

## Journal console (inchangé)

Progression et avertissements identiques à la feature 001 ; la clé API
n'apparaît jamais, y compris dans les rapports.
