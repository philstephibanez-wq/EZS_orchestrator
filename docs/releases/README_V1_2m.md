# EZS Orchestrator 1.2m — Assistant Web distant

- La commande distante Démarrer assistant lance le Web canonique via scripts/start.cmd.
- Le singleton Web 1.3c reste l'unique propriétaire des ports 8712/8713.
- Le token LAB et le chemin SMB des modèles sont transmis au processus Web au démarrage, sans les inscrire dans le dépôt.
- La supervision RUNNING exige désormais Web + distributed-watch + profile-review-auto-watch.
- La commande distante Arrêter assistant appelle scripts/stop.cmd et vérifie que 8712/8713 sont libérés.
- Aucun changement scientifique.

## Standardisation des commandes de cycle de vie

- Entrée canonique de démarrage : `scripts\\start.cmd`.
- Entrée canonique d'arrêt : `scripts\\stop.cmd`.
- `launch.bat` et `stop.bat` restent présents pour compatibilité.
- VERSION reste `1.2m`.
- Aucun changement scientifique.

## Hotfix démarrage et cycle de vie

- Correction du f-string Python de supervision Assistant.
- scripts\start.cmd reste l’entrée canonique.
- scripts\stop.cmd arrête le Control Center puis le worker permanent.
- Protection contre tout kill d’un processus étranger sur 8700.
- Le splash lit VERSION.
- VERSION reste 1.2m.
- Aucun changement scientifique.

## Hotfix chemin source Assistant

- Source Assistant canonique : `H:\EZStudioLab_assistant`.
- `H:\EZStudio_lab` reste le dépôt LAB séparé pour les dépendances runtime scientifiques.
- Suppression de la dépendance obsolète au gitlink parent `EZStudioLab_assistant`.
- L'affichage de version et le statut de déploiement utilisent la source canonique.
- VERSION reste `1.2m`.
- Aucun changement scientifique.

## Déploiement Git propre de l'Assistant

- XPS utilise un clone Git propre de `EZStudioLab_assistant`.
- Le statut déployé est basé sur le `git HEAD` distant.
- Le runtime scientifique est séparé dans `C:\\EZStudioLab_assistant_runtime`.
- `vendor/` est réutilisé si `composer.lock` est identique.
- La supervision distante utilise les commandes canoniques `scripts\\start.cmd` / `scripts\\stop.cmd`.
- VERSION reste `1.2m`.
- Aucun changement scientifique.

## Suppression UI Python legacy Assistant

- Ne démarre plus `app/status_window.pyw` sur XPS.
- Ne crée plus la tâche `EZStudioLab Assistant Status`.
- Le stop nettoie encore cette ancienne tâche si elle subsiste.
- Le Web canonique conserve token LAB, URL LAB et racine modèles avant `scripts/start.cmd`.
- VERSION reste `1.2m`.
- Aucun changement scientifique.

## Web Assistant persistant hors session SSH

- Le Web n’est plus enfant direct de la session SSH.
- Tâche persistante `EZStudioLab Assistant Web` pour 8712/8713.
- Token protégé via DPAPI.
- RUNNING exige Web + distributed + profile.
- VERSION 1.2m inchangée; aucun changement scientifique.
