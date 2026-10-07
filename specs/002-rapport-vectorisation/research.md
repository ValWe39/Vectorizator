# Research: Rapport de traçabilité optionnel (`--rapport`)

Session 2026-10-07 — Phase 0. Aucun marqueur NEEDS CLARIFICATION ne
subsistait dans la spec : les quatre questions du handoff d'assessment
sont déjà tranchées par des défauts documentés (Assumptions du spec.md).
Les inconnues ci-dessous sont les choix techniques restants avant le
design. Toutes sont résolues.

Sources consultées : spec.md et artefacts d'assessment
(`.specify/assessments/rapport-vectorisation/`) ; code existant
(`src/vectorizator/{cli,output,config,counter}.py`) ; prior art du
research.md d'assessment (sidecars manifest/metadata en ML) ; artefacts
de la feature 001 (`specs/001-vectorisation-mistral-embed/`).

## R-01 : Format du rapport — objet JSON plat à cinq clés

- Decision : objet JSON plat, exactement cinq clés — `entrée`, `sortie`,
  `embed`, `dimension`, `nature` (noms de l'intake d'origine) ; UTF-8,
  indenté (2 espaces) pour lecture humaine, avec retour à la ligne
  final.
- Rationale : lisible à l'œil dans un éditeur et parsable par un script
  ; cinq clés figées par la spec (FR-004) ; l'indentation ne coûte rien
  à l'échelle visée (quelques dizaines d'octets).
- Alternatives considered : JSON compact une ligne — rejeté (moins
  lisible pour l'usage humain déclaré) ; JSON Lines / manifest global
  cumulatif — rejeté en assessment (Option C) ; clés anglaises —
  rejeté (l'intake fixe les noms français ; cohérence terminologique).

## R-02 : Nommage du rapport — même nom que la matrice, `.json`

- Decision : le rapport porte exactement le nom du fichier matrice
  avec l'extension `.json` (ex. matrice
  `016472351681860015-0042.npy` → rapport
  `016472351681860015-0042.json`), dans le même dossier de sortie. Le
  nom est dérivé de la même construction que la matrice
  (`build_output_name`), pas recalculé indépendamment.
- Rationale : le sidecar voyage avec la matrice (copie, déplacement) ;
  l'unicité du numéro d'occurrence garantit l'absence de collision,
  y compris avec les JSON d'entrée (le rapport porte un suffixe
  `-NNNN` qu'un JSON d'entrée n'a pas).
- Alternatives considered : suffixe distinct (`-rapport.json`) — rejeté
  (l'intake exige « le même titre que la matrice ») ; un manifest
  unique pour le lot — rejeté (assessment, Option C).

## R-03 : Contenu et types des cinq champs

- Decision :
  - `entrée` : nom du fichier JSON d'entrée seul (nom + extension
    `.json`, sans dossier ni chemin) — FR-005 ;
  - `sortie` : nom du fichier matrice avec son extension `.npy` ;
  - `embed` : valeur exacte passée à `--choix-techno` (identifiant du
    preset, ex. `mistral-embed-dim256-2510`) — FR-006 ;
  - `dimension` : entier, lu depuis le preset (mapping existant
    `config.MODELS`), pas codé en dur dans le rapport ;
  - `nature` : nom du dtype de la matrice effectivement écrite (ex.
    `float32`), lu depuis la matrice produite, pas depuis une constante.
- Rationale : chaque champ reflète l'exécution réelle, pas une valeur
  supposée ; les sources de vérité existent déjà (preset pour la
  dimension, matrice pour le dtype) — le rapport reste vrai si le dtype
  ou le panel de modèles évoluent.
- Alternatives considered : chemin absolu dans `entrée` — interdit
  (FR-009, fuite d'information machine) ; dimension codée en dur —
  rejeté (deviendrait fausse silencieusement) ; nature sous forme
  narrative (« flottants 32 bits ») — rejeté (nom du dtype = valeur
  exploitable par un script).

## R-04 : Point d'écriture dans le pipeline

- Decision : le rapport est écrit immédiatement après l'écriture
  réussie de la matrice, avant la suppression du checkpoint
  (FR-007) ; l'écriture vit dans `output.py` (fonction `save_report`)
  à côté de `save_matrix`, appelée depuis `cli.py` seulement quand le
  flag est actif.
- Rationale : colocaliser nommage matrice/rapport dans un seul module
  garantit la cohérence des noms (R-02) ; écrire avant la suppression
  du checkpoint conserve la possibilité de reprendre si l'écriture
  échoue.
- Alternatives considered : écrire le rapport depuis `cli.py` sans
  fonction dédiée — rejeté (duplication du nommage, non testable en
  unitaire) ; écrire le rapport en fin de lot — rejeté (FR-007 exige
  après la matrice ; un échec en cours de lot perdrait les rapports).

## R-05 : Échec d'écriture du rapport

- Decision : une erreur d'écriture du rapport (disque plein, droits
  insuffisants) compte le document en échec avec message explicite
  (FR-011) ; la matrice déjà écrite est conservée ; le lot continue
  selon les règles multi-input existantes ; pas de retry (erreur
  locale, pas transitoire réseau) ; le checkpoint n'est pas supprimé,
  laissant une reprise possible.
- Rationale : le coût API est déjà dépensé — détruire la matrice ne
  récupère rien ; les erreurs locales ne se corrigent pas en réessayant
  aveuglément ; le code de sortie reste celui des échecs documentaires
  (2) via le compteur d'échecs existant.
- Alternatives considered : échec global immédiat — rejeté (plus
  destructeur que la règle multi-input existante) ; ignorer
  silencieusement l'échec du rapport — rejeté (la traçabilité
  silencieusement absente est pire qu'un échec explicite).

## R-06 : Option CLI — flag booléen `argparse`

- Decision : `--rapport` est un flag booléen (`action="store_true"`,
  défaut `False`) aux côtés des options existantes ; aucune borne à
  valider ; l'aide documente le comportement (rapport JSON par matrice
  réussie).
- Rationale : stdlib, cohérent avec les cinq options existantes
  (feature 001, R-09) ; un booléen n'a pas d'état hors bornes ; la
  validation existante (FR-012) est inchangée car rien à borner.
- Alternatives considered : `--rapport on/off` avec valeur — rejeté
  (plus verbeux, aucun cas d'usage d'activation par défaut) ; variable
  d'environnement — rejeté (la spec exige une option CLI explicite).

## R-07 : Aucune nouvelle dépendance

- Decision : écriture via `json.dumps` + écriture fichier standard
  (stdlib) ; réutilisation du dossier de sortie déjà créé par
  `save_matrix`.
- Rationale : Constitution III et IV ; la valeur ajoutée ne justifie
  aucune dépendance ; tout reste testable hors réseau (SC-002).
- Alternatives considered : bibliothèque de sérialisation riche —
  rejeté (YAGNI, cinq champs scalaires).
