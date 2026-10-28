# v2.a50 — constat exécutable de purge et refus des fausses preuves

La suppression du dernier serveur Python par le mainteneur, commit `5c2a40c`, est préservée. Le contrat PHP v2.a47 qui exigeait l'existence de `server.py` était devenu erroné ; il exige désormais **son absence**, la conservation des scripts essentiels et la présence du candidat gateway PHP.

Le diagnostic de `bin/infrastructure.php` ne considère plus `python.exe` comme image attendue du gateway 8510 : le seul candidat cible est `php-cgi.exe`. Le PID enregistré peut cependant appartenir encore à un ancien runtime Python. **Une image différente de php-cgi doit apparaître comme non vérifiée**, jamais être réinterprétée comme un gateway PHP. Aucune action sur ce PID n'est autorisée.

Cette correction ne modifie ni les listeners, ni le lifecycle PROD historique, qui fait toujours référence à `server.py` ; `start` PROD reste **bloqué** depuis sa suppression. Ce blocage ne doit pas être masqué par un faux test OK. Le PHP-FastCGI a une recette isolée historique mais il manque son superviseur de production, l'attestation Windows complète et les tests réels SSO/médias/rollback. Aucune bascule ou arrêt non supervisé ne peut être effectué à partir de GitHub.

Recette MAIN : `php tests/LegacyLauncherPurge2A47ContractTest.php`, `php -l bin/infrastructure.php`, `php bin/infrastructure.php status` (lecture seule, noter notamment `ownership.checks.prod_gateway.verified`). Aucun nouveau test live n'a été exécuté à la publication. Ne lancer ni stop ni start PROD tant que le gestionnaire PHP n'est pas livré et certifié.

Prochain lot opérationnel obligatoire : lifecycle PROD Symfony et gestionnaire PHP-FastCGI, test sur ports isolés, validation du rollback, puis branchement du port 8510 et retrait de `prod_lifecycle.ps1`. Seuls `start.ps1` et `stop.ps1` resteront après recette complète.
