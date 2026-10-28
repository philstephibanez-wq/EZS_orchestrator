# v2.b11 — réconcilier les contrats après bascule réussie

MAIN 2026-10-28 : tests v2.b10 OK, test v2.b9 échoué car il exige le marqueur obsolète `EZS_CADDY_MEDIA_ROOT_ENV_MISSING_REFUSED`, remplacé dès v2.b10 par `EZS_CADDY_EXISTING_DEV_MEDIA_DIRECTORY_MISSING`. Bascule Caddy DEV réellement réussie : 8790=200, 8502=200, 8852=200, 8702=302, 8712=200, marqueur final OK. Aucun test de SSO post-bascule ni du métier Assistant/worker/Qwen encore rapporté.

Correctif documentaire/test uniquement : actualisation du test existant avec le contrat actuel, aucun changement de code runtime, Caddy, application, science ou PROD. Vérification MAIN : `git pull --ff-only origin master`; `php tests/CaddyLabAssistantCutover2B9ContractTest.php`; `php tests/CaddyLabMediaResolution2B10ContractTest.php`. Ne pas relancer apply, qui a déjà réussi. Contrôle navigateur LAB/Assistant et worker restent ouverts.
