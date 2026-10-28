# v2.a57 — STOP Orchestrator force la maintenance PROD

Décision mainteneur : `stop.ps1` doit forcer la maintenance d'EZScore PROD, mais **ne pas arrêter de processus PROD**. Les opérations de retour au mode normal lors de `start.ps1` ne sont pas automatiques pour le moment : décision reportée.

Le script STOP appelle une entrée PHP durable `bin/prod_mode.php maintenance` utilisant le service existant `ProdModeService::apply('maintenance')`. Ce service impose verrou exclusif, vérifie la réponse protocole du gateway et constate le HTTP 503 de la façade publique. **Si l'étape de maintenance échoue, STOP refuse d'arrêter DEV**. Après confirmation, STOP appelle le lifecycle DEV existant. Le gateway PHP PROD 8510/18515 et Caddy 8501 / interne 8511 / FastCGI 8512 restent actifs.

`bin/prod_mode.php status` donne l'état en lecture seule ; `bin/prod_mode.php normal` est une action PROD explicite et nécessite backend sain. Aucune variable de recette, Python ou script temporaire. Un contrat statique de séquencement et fail-closed est ajouté.

Test MAIN sans interruption : `git pull --ff-only origin master`; `php -l bin/prod_mode.php`; `php tests/StopForceMaintenanceContractTest.php`; `php bin/prod_mode.php status`. Le véritable `stop.ps1` n'est à exécuter que lorsque l'indisponibilité publique en maintenance est acceptée. Aucun test de STOP réel effectué à la publication ; son résultat doit être communiqué dans l'issue.

Point ouvert : démarrage DEV n'enlève pas automatiquement la maintenance PROD (par choix explicite du mainteneur « on verra dans le futur »). Scripts de lifecycle historiques toujours présents et cible deux scripts PS1 non atteinte.
