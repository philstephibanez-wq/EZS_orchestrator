# Recette Caddy + PHP-FastCGI isolée — v2.a8

## Objet
Valider le bon accueil Symfony root : `templates/infrastructure/index.html.twig`, panneau GPU et quatre pavés DEV/PROD/LAB/Assistant, avec CSS et JS correctement servis. Le template historique inactif `legacy_home.html.twig` est retiré ; son ancien test de parité statique aussi.

## Cible et isolation
Caddy `config/caddy/Caddyfile.orchestrator-root-preview` existant : `127.0.0.1:8890` → PHP-CGI `127.0.0.1:8891`, docroot `H:/EZS_orchestrator/public`. Aucune modification des Caddyfiles actifs `8790/8791` ou `8501/8502`. La recette n'est pas un basculement d'exploitation et n'utilise pas `php -S`.

Avant lancement, confirmer les deux ports libres et la présence des exécutables `H:\PHP\php-8.5-x64\php-cgi.exe`, `H:\Caddy\caddy.exe`, `public/index.php` et `vendor/autoload.php`. Refuser les ports occupés, ne jamais tuer un PID inconnu. Exécuter php-cgi et Caddy manuellement depuis deux consoles de recette ouvertes sur MAIN ; les arrêter avec Ctrl+C depuis leurs consoles uniquement. Aucun nouveau script permanent.

## Gates
1. `caddy validate --config config/caddy/Caddyfile.orchestrator-root-preview --adapter caddyfile`.
2. `php tests/SymfonyRootHttpKernelTest.php`, `php tests/SymfonyHistoricHomeRuntimeTest.php`, `php tests/SymfonyLegacyWebRetirementGateTest.php`.
3. PHP-CGI sur 8891, Caddy preview sur 8890, `php tests/SymfonyRootPreviewProbeTest.php` : GET / donne les quatre pavés et le panneau GPU ; /api/status affirme source Symfony, /api/jobs renvoie 503 explicite ; /assets/ezs-infrastructure.css doit être `text/css`, et /assets/ezs-gpu-monitor.js `javascript`.
4. Contrôler visuellement les libellés français et la mise en page, puis arrêter les deux consoles.

## Limites
Sonde GPU 503 encore en cours de diagnostic HTTP ; ne pas la maquiller. Actions et queues historiques non migrées. Ce lot ne répare pas les lanceurs start/stop d'exploitation, l'ownership PID automatisé ni la garantie zéro fenêtre Windows 11. Aucune suppression de `web/` autorisée par cette seule recette.
