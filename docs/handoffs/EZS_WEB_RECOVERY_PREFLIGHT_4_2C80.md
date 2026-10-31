# EZS Web recovery — preflight 4.2c80

## Faits vérifiés
- Base GitHub master 4.2c79.
- Intention JSON et SQLite attestées RUNNING pour root/dev/lab/assistant/prod par opérateur ; maintenance PROD ON.
- Tick manuel antérieur a restauré quatre FastCGI, mais les lancements depuis php-win / ordonnanceur ont ouvert des fenêtres et volé le focus.

## Portée et limites
- Ajout endpoint d'observabilité exclusivement GET, limité au DEV local.
- jQuery appelle l'endpoint à l'ouverture Infrastructure ; il ne commande aucun processus.
- AUCUNE récupération FastCGI n'est activée par cette étape ; pas de modification des intentions, ROOT, Caddy, PROD.
- L'absence d'une chaîne Windows parent/enfants qualifiée zéro focus BLOQUE la prochaine étape de récupération réelle.

## Recette
- Lint PHP, test PHPUnit, lint Twig et visibilité de la mention d'attente.
- Cette étape ne constitue PAS une recette de récupération FastCGI ni zéro-focus des processus enfants.
