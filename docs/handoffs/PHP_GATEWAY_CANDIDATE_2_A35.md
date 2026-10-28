# v2.a35 — passerelle PHP candidate, sans bascule PROD

La passerelle Python `runtime_components/prod_gateway/server.py` reste **active et intacte** sur le port 8510.

Nouvelle candidate de test : `runtime_components/prod_gateway_php/router.php` (PHP 8.5). Ne pas exposer publiquement, ni démarrer sur 8510. Test local sur un port séparé, par exemple :

```powershell
php -l runtime_components\prod_gateway_php\router.php
php tests\PhpGatewayCandidateContractTest.php
# Dans un terminal séparé uniquement, facultatif :
H:\PHP\php-8.5-x64\php.exe -S 127.0.0.1:8513 -t runtime_components\prod_gateway_php runtime_components\prod_gateway_php\router.php
```

`Invoke-WebRequest http://127.0.0.1:8513/__ezscore_gateway_status -UseBasicParsing` doit refléter la configuration active (ne pas modifier cette configuration pour le test). Tester maintenance et fonctionnement normal **sans basculer PROD**, via configuration de test isolée lors d'une prochaine version. Le serveur web intégré PHP ne garantit pas une parité de streaming, headers, cookies, SSO et requêtes média : **non homologué pour PROD**.

La bascule requiert une recette fonctionnelle complète et un gestionnaire de processus, une reprise contrôlée et un rollback. Aucune purge du `.py` avant cela.
