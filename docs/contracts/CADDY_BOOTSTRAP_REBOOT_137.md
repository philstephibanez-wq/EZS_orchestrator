# Démarrage Caddy après reboot — v1.3a(7)

Le démarrage canonique scripts/start.cmd -> launch.bat -> scripts/launch_hidden.ps1 assurait le service permanent et le Control Center mais n'appelait pas le module canonique caddy_manager pour restaurer les reverse proxies. Après redémarrage Windows, DEV PHP 8602 pouvait renvoyer HTTP 200 tandis que Caddy DEV 8502 restait arrêté.

Correctif : après le service permanent, demander à caddy_manager.cli start de réconcilier DEV, PROD, LAB, dans cet ordre, par CaddyManager.start. Ce dernier conserve les processus owned/adopted et adopte les orphan_exact ; tout processus étranger est refusé. Vérification HTTP obligatoire dans la CLI pour start. Les erreurs par cible sont consignées dans logs/caddy-start.log et logs/control-center-error.log. Echec DEV signalé comme échec du lancement, les autres cibles ont néanmoins été tentées.

Ce correctif ne promet pas une surveillance continue après démarrage : il corrige la remise en route après reboot/start.cmd ; la supervision récurrente est un chantier distinct.

Tests : python -m unittest tests.test_caddy_bootstrap_137 ; analyse syntaxique PowerShell via [System.Management.Automation.Language.Parser]::ParseFile sur MAIN. Tests Windows et reboot réel à exécuter sur MAIN. Ne pas redémarrer les services PROD ou LAB pour le test ; vérifier les ports/HTTP existants puis utiliser le démarrage canonique uniquement quand approprié.
