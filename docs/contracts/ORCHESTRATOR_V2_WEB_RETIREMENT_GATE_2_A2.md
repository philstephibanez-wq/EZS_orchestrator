# Contrat de retrait sûr de web/ — v2.a2

## Objet
Prévenir la répétition de la régression où la suppression de `web/.gitignore` expose dans Git des fichiers générés (`web/vendor/`, `web/var/`, `web/config/reference.php`) et où des chemins Caddy actifs sont basculés avant recette fonctionnelle.

## Décisions exécutoires
- La racine `.gitignore` contient les protections historiques, indépendamment de la présence de `web/.gitignore`. Celui-ci reste lui aussi suivi pendant la transition.
- Aucun nettoyage de `web/` ni déplacement des tests historiques dans cette livraison. Les fichiers `web/vendor/`, `web/var/`, les secrets locaux et `web/config/reference.php` ne doivent jamais être indexés.
- Les Caddyfiles actifs conservent pour l'instant le docroot `H:/EZS_orchestrator/web/public`. Aucune modification des ports 8790/8791, 8502 ou des instances Caddy.
- Le lanceur V2 reste fail-closed ; aucune substitution par `php -S`, Python ou un serveur temporaire n'est autorisée.
- La suppression définitive de `web/` exige, dans un même lot ultérieur, la vérification des chemins actifs, les tests HTTP réseau Symfony root, la parité des APIs et fonctions requises, une recette lifecycle et PID sur MAIN, et un rollback testé. Les travaux queues/Assistant/jobs/PROD restent interdits à la bascule sans preuve.

## Tests permanents
`php tests/SymfonyLegacyWebRetirementGateTest.php` contrôle les exclusions, le maintien du dossier historique, le docroot Caddy, le blocage du lanceur et l'état non migré des jobs. `git check-ignore -v web/vendor/autoload.php web/var/cache/dev/test.php web/config/reference.php` doit produire des règles issues du `.gitignore` racine. Après une suppression autorisée, le contrat et le test devront être remplacés ensemble par des tests d'absence et de parité.

## Validation et statut
Revue statique des sources GitHub sur `master` avant publication. **Aucun test Windows, aucune bascule HTTP réelle ni contrôle de service effectués dans ce lot.** Il s'agit d'une protection préventive vérifiable, pas d'une migration fonctionnelle ou d'une certification de retrait. Les opérations effectives sont différées.
