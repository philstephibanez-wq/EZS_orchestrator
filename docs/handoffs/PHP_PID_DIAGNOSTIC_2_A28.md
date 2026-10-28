# v2.a28 — diagnostics de PID en PHP natif

`php bin/infrastructure.php status` expose des diagnostics PID via netstat.exe et tasklist.exe invoqués directement depuis PHP sans cmd.exe ni PowerShell. Vérification du PID occupant le port et du nom de l'image. Mode fail-closed : l'identité complète (chemin binaire, ligne de commande, heure de création) n'est pas certifiée, et **aucune opération destructive ne doit utiliser ces informations seules**. Aucune modification du lancement/arrêt, DEV/PROD inchangés. Validation MAIN nécessaire avant de migrer les contrôles stricts des start/stop.
