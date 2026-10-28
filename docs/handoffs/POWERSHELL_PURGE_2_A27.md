# Purge 2.a27 — statut PHP canonique

Supprimé : `scripts/status.cmd`, ancien wrapper invoquant `v2_lifecycle.ps1 -Action status`.

Remplacement : `php bin/infrastructure.php status`. Commande disponible en PHP depuis 2.a25. La recette doit vérifier les réponses DEV/PROD, sans prétendre attester les PID (le statut actuel vérifie uniquement les ports et métadonnées).

Ne pas supprimer encore `v2_lifecycle.ps1`, `prod_lifecycle.ps1`, `infrastructure_restore.ps1`, `start.cmd` ou `stop.cmd` : des dépendances actives de lancement/arrêt existent toujours, notamment `start.ps1` et `stop.ps1` vers `v2_lifecycle.ps1`. Les retirer nécessite la migration de la propriété des processus, des reprises et le contrôle des points d'entrée externes. Aucun processus n'est redémarré lors de cette purge.
