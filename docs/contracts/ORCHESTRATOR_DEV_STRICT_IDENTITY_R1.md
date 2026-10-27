# v1.3b19 — Identité stricte backend EZScore DEV

Le port 8602 est inspecté en lecture seule. Classification `legacy_exact` seulement si PID du listener, chemin exact `H:\\PHP\\php-8.5-x64\\php.exe`, `-S 127.0.0.1:8602` et document root `H:\\EZScore_dev\\public` coïncident. Toute divergence devient `foreign`, échec lecture `unknown`, port absent `absent`. Ne pas interpréter `legacy_exact` comme une autorisation de tuer/adopter automatiquement, ni comme une preuve cryptographique d'identité.

Ce contrôle explicite que le backend détecté est le serveur historique `php -S` incompatible avec la cible Caddy DEV partagé + FastCGI. Les boutons restent désactivés avant livraison d'un lanceur canonique intégré et authentifié. Aucun service PROD ni Caddy modifié.

Tests MAIN : `php web/tests/DevBackendOwnershipTest.php`, lint Twig/container, GET API et détails de la carte DEV. Le test simule PID étranger, exécutable divergent, port préfixe trompeur et mauvaise racine.
