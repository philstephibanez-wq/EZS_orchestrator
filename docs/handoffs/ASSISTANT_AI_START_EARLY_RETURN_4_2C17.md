# 4.2c17 — Correctif du START déjà actif

Observation utilisateur : START répond `EZS_DEV_ALREADY_RUNNING_VERIFIED`, `EZS_DEV_APPS_ALREADY_RUNNING_VERIFIED`, `EZS_LA_BACKENDS_ALREADY_RUNNING_VERIFIED`, puis termine sans `EZS_AI_START_OWNED_READY_8720`. Cause dans `scripts/start.ps1` : le chemin DEV déjà prêt contient un `return` avant la fonction IA ajoutée en fin de fichier.

Correctif : déclaration de `Invoke-EzsAssistantAiLifecycle` avant les branchements, et appel IA explicitement ajouté après le contrôle LAB sur le chemin déjà prêt. Le chemin normal de fin reste en place. Une expression de lecture du propriétaire du port est corrigée. Aucune modification de STOP, LAB, DEV, PROD ou Assistant.

Préflight de reprise : lint AST PowerShell et test `tests/AssistantAiStartEarlyReturn42C17ContractTest.php`. Puis un START réel lorsque 8720 est libre, avec contrôle `/health` et status 8712. Le démarrage réel n'est **pas** attesté par le commit ; ne consommer aucun job LAB. Échec potentiel de toute phase antérieure reste fail-closed.
