# V2.a47 — purge des lanceurs obsolètes et inventaire exhaustif

Inventaire de l'arbre Git `master` effectué avec l'API GitHub `git/trees/master?recursive=1` (242 fichiers, `truncated=false`) avant modification :

- Python : **1** source, `runtime_components/prod_gateway/server.py`.
- PowerShell : **2** sources, `scripts/prod_lifecycle.ps1` et `scripts/infrastructure_restore.ps1`.
- BAT : `launch.bat` et `stop.bat`.

## Suppression non destructive

Suppression de `scripts/infrastructure_restore.ps1`, qui dépend de `scripts/v2_lifecycle.ps1` déjà retiré ; de `launch.bat` et `stop.bat`, qui appellent `scripts/start.cmd` et `scripts/stop.cmd`, absents de l'arbre. Aucun de ces chemins ne dispose encore d'un remplacement DEV opérationnel. L'historique Git conserve le contenu supprimé.

## Deux bloqueurs PROD préservés

- `runtime_components/prod_gateway/server.py` fournit actuellement le gateway Python PROD, port 8510 ; la recette PHP FastCGI v2.a41e, bien que réussie, **ne prouve ni SSO ni médias réels**.
- `scripts/prod_lifecycle.ps1` contient encore `start`, `stop`, `status`, `maintenance`, `normal` et `repair-fastcgi`, et lance explicitement le gateway Python.

**Ne pas supprimer ces deux fichiers maintenant : PROD risquerait de ne plus redémarrer.** Aucune migration de ces opérations n'est prétendue achevée. Les services actuellement en mémoire ne sont pas affectés par ces suppressions Git, mais aucune reprise après redémarrage n'est garantie par le code Symfony V2 incomplet.

## Recette MAIN

`php tests/LegacyLauncherPurge2A47ContractTest.php` ; `git ls-files '*.py' '*.ps1'` pour confirmer la liste résiduelle ; contrôle statique `git diff --check`. Tests nouveaux non exécutés sur MAIN à publication. Aucun déploiement, restart, queue ou bascule autorisés. Ensuite : remplacer complètement et tester la passerelle PROD et le lifecycle Symfony, puis retirer les **deux dernières sources** dans la même livraison de bascule validée.
