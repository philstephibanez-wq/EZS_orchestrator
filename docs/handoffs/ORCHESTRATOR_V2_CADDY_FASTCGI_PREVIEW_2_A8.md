# Handoff v2.a8 — Caddy/FastCGI preview et accueil à quatre pavés

Décision utilisateur : lancer la recette Caddy+PHP-FastCGI avec les bons templates et retirer le template legacy abandonné. Vérification GitHub : `HomeController` rend déjà `infrastructure/index.html.twig`, sonde `_gpu_monitor.html.twig`, quatre pavés. Le Caddyfile preview isolé est déjà correct ; aucun changement Caddy requis. Les CSS et JS sont sous `public/assets` ; un `php -S` mal routé avait servi le CSS comme `text/html`.

Livraison : retrait de `templates/infrastructure/legacy_home.html.twig` et du test statique obsolète, test durable de l'accueil actif, extension de la sonde HTTP pour vérifier MIME CSS/JS, contrat d'activation isolée. Aucun chemin de service actif modifié, aucun autre fichier `web/` supprimé, protections `.gitignore` inchangées.

Validation statique GitHub uniquement à publication. MAIN doit contrôler lint PHP, lint Twig, Caddy validate, disponibilité ports et prévisualisation réelle, puis arrêter les deux processus de recette. Le 503 GPU en HTTP reste distinct et non résolu. Aucune certification de parité totale, d'ownership automatisé ni de non-apparition de fenêtre console.
