# v1.3b327 — point d'entrée PROD indépendant du répertoire courant

Corrige le chargement des modules `prod_lifecycle` par `scripts/prod-edge-start.py` quand le fichier est lancé directement par Python : insertion explicite de la racine du dépôt dans `sys.path`. Test statique étendu. Aucun processus et aucun Caddyfile actif modifiés. Recette Python et opération `start.cmd` à réaliser sur MAIN après tests.
