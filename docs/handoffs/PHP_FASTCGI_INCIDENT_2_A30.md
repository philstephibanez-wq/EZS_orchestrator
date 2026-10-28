# v2.a30 — diagnostic incident PHP-FastCGI DEV

Commande **lecture seule** : `php bin/infrastructure.php fastcgi-incident`.

Expose le PID attendu dans le fichier d'état, la liste (maximum 5) des fichiers stderr existants lors des démarrages et les événements Windows Application des dernières 24 heures concernant PHP trouvés parmi 25 événements de type 1000/1001/1002/1026. Les événements sont indicatifs et ne certifient pas le motif de sortie ; aucune réparation, aucun kill. Aucun nouveau PS1/CMD.

Le retrait de `v2_lifecycle.ps1` est bloqué : `start.ps1` et `stop.ps1` le délèguent encore ; celui de `prod_lifecycle.ps1` est bloqué par les démarrages/arrêts PROD ; `infrastructure_restore.ps1` reste un point d'entrée combinant des actions encore non migrées. Il n'est pas sûr de supprimer deux scripts dans cette version. Aucun redémarrage PROD/DEV n'est effectué.
