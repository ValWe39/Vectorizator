# Data Model: Rapport de traçabilité optionnel (`--rapport`)

Session 2026-10-07 — Phase 1. Entités dérivées de la spec et de
research.md. Ce document complète le data-model de la feature 001
(`specs/001-vectorisation-mistral-embed/data-model.md`), inchangé par
la présente feature, sauf la relation 1:1 ajoutée en §5.

## 1. Rapport de traçabilité

Fichier JSON sidecar d'une matrice de sortie ; produit seulement quand
l'option `--rapport` est active (désactivée par défaut).

- `entrée` : chaîne — nom du fichier JSON d'entrée, seul (nom +
  extension `.json`), sans dossier ni chemin absolu. Exemple :
  `016472351681860015.json`.
- `sortie` : chaîne — nom du fichier matrice avec son extension.
  Exemple : `016472351681860015-0042.npy`.
- `embed` : chaîne — identifiant exact du modèle, valeur de
  `--choix-techno` (un des presets de `config.MODELS`).
- `dimension` : entier — dimension des vecteurs du preset utilisé
  (1024, 256 ou 128).
- `nature` : chaîne — nom du dtype des flottants de la matrice écrite
  (`float32` en l'état), lu depuis la matrice produite.

- `nom` : même nom que la matrice, extension `.json` (ex. matrice
  `016472351681860015-0042.npy` → rapport
  `016472351681860015-0042.json`), dérivé de la même construction de
  nom que la matrice.
- `emplacement` : dossier de sortie (`output` par défaut), à côté de la
  matrice.
- `format` : objet JSON plat à cinq clés, UTF-8, indenté (2 espaces),
  retour à la ligne final ; aucune clé supplémentaire, aucun
  horodatage, pas de version de schéma.

Validation : cinq clés présentes et cohérentes avec l'exécution
concernée ; `dimension` ∈ {1024, 256, 128} selon `embed` ; `sortie`
est le nom de la matrice écrite dans la même exécution ; jamais de clé
API ni de chemin absolu (FR-009).

Interdits : modification après écriture (le rapport est immuable),
écrasement d'un rapport existant (un numéro d'occurrence n'est jamais
réutilisé), copie cachée ailleurs (rétention contrôlée par
l'utilisateur, comme la matrice).

## 2. Relation avec la matrice de sortie

La matrice (feature 001, §5) gagne une relation :

- 1 matrice `.npy` réussie → 0 ou 1 rapport : 1 si `--rapport` active
  à l'exécution, 0 sinon.
- Un document en échec ne produit ni matrice ni rapport (FR-008).
- Le rapport est écrit après la matrice (FR-007) et hérite de son
  unicité par le numéro d'occurrence : re-vectoriser un document
  consomme un nouveau numéro, donc une nouvelle paire matrice/rapport
  distincte ; l'ancienne paire n'est ni modifiée ni supprimée.

## 3. Option CLI `--rapport`

- Flag booléen, défaut inactif ; activé uniquement par la présence de
  `--rapport` sur la ligne de commande.
- Aucune borne, aucune validation au-delà du parsing.
- Sans le flag : sorties, messages console et codes de sortie
  strictement identiques au comportement sans la feature (FR-002).

## 4. Échec d'écriture du rapport

- Une erreur locale d'écriture (disque, droits) après l'écriture de la
  matrice : le document est compté en échec avec message explicite, la
  matrice est conservée, le checkpoint reste en place (reprise
  possible), le lot continue (FR-011).
- Aucun retry : l'erreur est locale, pas transitoire réseau.

## Cycle de vie d'un rapport

```text
(document reussi) -> matrice .npy ecrite
    -> si --rapport : rapport JSON ecrit a cote (meme nom, .json)
    -> checkpoint supprime (inchange, feature 001)
rapport : immuable, jamais reecrit ; supprime par l'utilisateur
          en meme temps que la matrice, s'il le souhaite
```
