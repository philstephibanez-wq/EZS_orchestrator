# 4.2c18 — Correction de la recette contractuelle

Preuves mainteneur : version 4.2c17, syntaxe AST des deux scripts OK ; le test PHP échoue en `EARLY_RETURN_BYPASS` alors que START réel annonce `EZS_AI_START_OWNED_READY_8720`, GET /health retourne `ok`, Assistant retourne `READY`, interface affiche les deux statuts prêts, file LAB job 193 non consommé.

Cause : le test contenait une expression régulière fragile et mal échappée pour vérifier l'ordre d'exécution de la branche « DEV déjà actif ». Remplacement par une inspection déterministe des segments et de leur ordre à l'intérieur de cette branche. Seul le test, VERSION et ce handoff changent. START/STOP et exécutable IA intacts.

Nouvelle validation requise : `php tests/AssistantAiStartEarlyReturn42C17ContractTest.php` ; les contrôles Windows précédents restent des observations réelles, mais aucune recette supplémentaire n'est revendiquée. Le stop attesté reste non testé et ne doit pas être déclenché pendant cette correction.
