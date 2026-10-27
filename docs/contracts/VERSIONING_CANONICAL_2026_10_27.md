# Correctif de conformité des versions — 2026-10-27

## Décision
Format canonique obligatoire : release `MAJOR.MINOR` ; fix `MAJOR.MINORa`, puis `b`, ... `z`, `aa`, etc. Aucun suffixe numérique parenthésé pour une nouvelle livraison.

## État et anomalie
Des commits antérieurs, dont `[v1.3a(24)]`, `[v1.3a(25)]` et `[v1.3a(26)]`, employaient le format historique parenthésé malgré la règle de `AGENTS.md`. Les exemples de la section « messages de commit » ont entretenu la contradiction. Ne pas réécrire l'historique partagé.

## Remise en conformité
La version canonique repart à `1.3b` (fix suivant dans la série 1.3). La valeur du fichier `VERSION` et le préfixe du commit concordent. Les anciennes mentions numériques dans les notes historiques ne sont pas des versions réutilisables. Les prochaines évolutions incrémentent le suffixe, sans sous-compteur.

## Validation et limites
Inspection documentaire du contrat et du HEAD GitHub uniquement. Aucun test d'exécution, démarrage de service, publication de rapport ou job scientifique. Les écarts de version présents dans les autres dépôts restent à inventorier indépendamment, sans modification de leurs versions dans ce correctif.
