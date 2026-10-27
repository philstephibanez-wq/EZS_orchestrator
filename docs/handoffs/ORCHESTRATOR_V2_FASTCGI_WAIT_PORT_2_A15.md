# v2.a15 — correction Wait-Port sous Windows

MAIN v2.a14 : diagnostic `launched_pid=31100 alive=True listener_pids=31100` malgré `EZS_START_FASTCGI_FAILED_DIAGNOSTIC_AVAILABLE`. Le processus et le port sont correctement appariés au moment du diagnostic. Le garde `Wait-Port` abandonnait immédiatement au premier listener observé avec un PID différent ou transitoirement non résolu ; il produisait donc un faux échec de démarrage.

Correction : attendre jusqu'à 10 secondes la correspondance effective entre port et PID, interrompre seulement si le processus lancé n'existe plus, puis effectuer une dernière lecture du port. Les vérifications de propriétaire, les refus d'occupation préexistante, les contrôles singleton et l'arrêt de v2.a13 sont inchangés. Le test statique vérifie l'absence de rejet immédiat d'un listener transitoire.

Validation effectuée : revue des sources GitHub ; tests PowerShell/PHP et démarrage réel à exécuter sur MAIN. Prérequis : arrêter le php-cgi manuel dans sa propre console et vérifier 8791 libre ; contrôler ensuite start/status. Aucun processus PROD ciblé. `web/` demeure en attente de nettoyage.
