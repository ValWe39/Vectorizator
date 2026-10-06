# Bug Verification: Nom de sortie dérivé du nom de fichier du JSON

- **Slug**: titre-depuis-nom-json
- **Tested**: 2026-10-06
- **Assessment**: ./assessment.md
- **Fix**: ./fix.md
- **Result**: verified

## Summary

Le symptôme ne se reproduit plus : la sortie du scénario réel est
désormais nommée depuis le nom de fichier du JSON (`016472351681860015-0002.npy`,
18 caractères, sans extension), et non depuis `document.title`. La
suite complète de régression (104 tests, lint, conformité) passe sans
régression.

## Checks Performed

| Check | Commande | Résultat | Notes |
|-------|----------|-----------|-------|
| Reproduction | `vector` sur l'exemple (API réelle) | pass | exit 0 |
| Sortie | `numpy.load` + inspection | pass | (247, 1024) ; compteur 0002 |
| Tests | `python -m pytest` | pass | 104 passed |
| Lint | `ruff check` + `format --check` | pass | tous verts |
| Conformité | `check_constitution.py`, markdownlint | pass | OK / Passed |

Détails : reproduction = `vector Examples/016472351681860015.json` ->
`output/016472351681860015-0002.npy` ; les 104 tests incluent ceux du
nommage (18/stem/sans extension) ; conformité via
`check_constitution.py --diff HEAD` et `markdownlint-cli2`.

## Output Excerpts

```text
$ vector Examples/016472351681860015.json
[OK] Examples\016472351681860015.json -> output\016472351681860015-0002.npy
exit: 0

contenu output/ : ['016472351681860015-0002.npy', 'Introduction aux Emb-0001.npy']
shape : (247, 1024) | dtype : float32
compteur : 0002

$ python -m pytest
104 passed in 1.91s
```

## Residual Risks

- L'ancien artefact pré-fix `output/Introduction aux Emb-0001.npy`
  coexiste avec la nouvelle sortie (dossier gitignoré, sans impact) ;
  suppression manuelle au choix.
- Le compteur local est passé à 0002 : les deux numéros consommés
  correspondent bien aux deux exécutions réelles (0001 pré-fix,
  0002 post-fix) — comportement attendu du FR-011.
- La validation a porté sur un exemple de stem de 18 caractères
  exactement ; les stems plus longs/courts et la sanitisation sont
  couverts par les tests automatisés, pas par l'exécution réelle.

## Recommendation

Close the bug — verified end-to-end : reproduction réelle post-fix
conforme, suite de tests et de lint intégralement verte. Prochaine
étape : committer l'implémentation complète et le correctif via
`/commit-push-ameliore 002-Noyau 5 phrases`.
