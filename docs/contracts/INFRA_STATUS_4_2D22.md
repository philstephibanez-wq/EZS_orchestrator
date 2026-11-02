# Infrastructure 4.2d22 — état transport ≠ santé applicative

## Constat
Orchestrator 4.2d21 affichait « Répond » sur un HTTP 302 de LAB alors que `/workbench/profile` renvoyait 500 ; les boutons pouvaient être désactivés après un échec ponctuel de l'API de permissions tout en conservant les derniers libellés de RUNNING.

## Portée
Ce lot distingue explicitement « HTTP accessible », « HTTP 302 · redirection », « HTTP en erreur ». **Il ne crée pas de sonde métier PROFILE** : un 302 de façade ne prouve ni succès ni échec fonctionnel de LAB.
Les commandes restent désactivées en cas de permissions non vérifiables ; l'état du contrôle est exposé dans `data-ezs-probe` et le motif apparaît dans le retour de supervision et dans les titres des boutons. Aucune permission n'est inventée.

## Impacts
- JS frontend et lien de cache d'asset Twig, aucun changement de route serveur ni de queue.
- Aucun appel de démarrage/arrêt, aucune mutation des ressources, aucune influence sur PROD.
- Même cadence 15 secondes, mêmes délais et même CSRF.
- Risque d'API intermittente : commandes restent volontairement désactivées. L'UI doit permettre de le diagnostiquer.
- Retour arrière : sauvegardes sous `H:\temp\EZS_INFRA_4_2D22_BACKUP`, restaurées seulement sur décision.

## Preuves requises
PHPUnit complet, lint container, `git diff --check`; recette HTTP UI sur MAIN : réponse 200 et 302, API de commandes valide, indisponible puis restaurée ; aucune commande POST lors du test. Surveiller la console JS et les badges sur les cartes DEV/LAB/Assistant. Le test PHPUnit source est un test de contrat statique ; la validation dynamique reste obligatoire.
