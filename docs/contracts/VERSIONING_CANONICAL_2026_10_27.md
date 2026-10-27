# Convention de versionnement — décision du mainteneur (27 octobre 2026)

## Format canonique
- Release : `1.3`.
- Série corrective et compteur simplifié sans parenthèses : `1.3b0`, `1.3b1`, `1.3b2`.
- Nouvelle série : `1.3c0`. Nouvelle release : `1.4`.
- Le préfixe du commit doit correspondre strictement à `[vVERSION]`.
- Chaque livraison regroupe le changement durable, la mise à jour de `VERSION`, les tests et la documentation, sans scripts temporaires dans le dépôt.

## Correction historique
`1.3a(24)`, `1.3a(25)`, `1.3a(26)` étaient les anciennes notations ; une tentative incorrecte `1.3b` a ensuite été publiée. Ces références restent inchangées dans l'historique Git. Le mainteneur a validé le format **`1.3b0`** comme version canonique actuelle. Ne pas réécrire de commits publiés.

## Périmètre et validation
Correction du contrat documentaire et du fichier `VERSION` uniquement. Vérification statique des valeurs dans les fichiers GitHub ; aucun test runtime exécuté, aucun service/job démarré. Les autres dépôts conservent leur état tant qu'une décision explicite ne les aligne pas.
