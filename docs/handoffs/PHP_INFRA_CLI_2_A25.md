# v2.a25 — progression vers PHP

Après le push utilisateur v2.a24 sur master, ajout d'une commande native PHP pour preflight et status sans mutation de processus : `php bin/infrastructure.php preflight` et `php bin/infrastructure.php status`. Préflight vérifie les fichiers nécessaires et Caddy valide les trois configurations ; status expose présence des métadonnées et écoute TCP, sans prétendre vérifier l'identité du propriétaire des ports. Les opérations normal/maintenance sont déjà servies par Symfony en PHP.

Cette étape ne retire aucun PS1 ou wrapper CMD, car start.ps1/stop.ps1 délèguent toujours à v2_lifecycle.ps1 et la recette de démarrage et d'arrêt doit être maintenue. L'état opérationnel PROD/DEV et le SSO sont préservés. Prochaine étape : remplacer sous recette la supervision d'identité des processus et les lanceurs, puis retirer les scripts et tests hérités après validation sur MAIN. Aucun redémarrage déclenché par ce commit.
