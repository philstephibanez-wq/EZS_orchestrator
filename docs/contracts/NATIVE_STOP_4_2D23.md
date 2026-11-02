# Orchestrator 4.2d23 — Arrêt natif Windows

## Incident confirmé

Les tentatives HTTP STOP DEV et LAB sont acceptées puis journalisées `failed_com_exception`. Les intentions persistent en STOPPED alors que les processus restent RUNNING. La méthode `nativeTerminate` appelait `Win32_Process.Terminate(0)` via COM.

## Solution

Conserver l'attestation WMI (exécutable, arguments, horodatage de création et ports) immédiatement avant l'arrêt. Remplacer uniquement la terminaison COM par l'exécutable Windows `taskkill.exe /PID <PID> /F`, appelé directement par Symfony Process, sans shell, sans `/T` et sans joker. Attendre de manière bornée la disparition du PID **et** la libération du port géré. L'API STOP refuse HTTP 200 tant que le groupe n'est pas attesté STOPPED. L'intention STOPPED reste persistante même si l'arrêt échoue ; aucun retry ou START implicite.

## Impact et limites

Périmètre DEV/LAB/Assistant uniquement. PROD et ROOT inchangés. Le mécanisme d'arrêt emploie l'exécutable Windows déjà présent dans `cleanupRootResidual()`. Les permissions du compte Windows et la gestion de PID recyclé doivent être vérifiées par recette réelle; le risque résiduel entre l'attestation et `taskkill` reste celui d'une fenêtre de changement d'identité et exige observation du résultat. En cas de refus ou d'incertitude, aucun arrêt générique ni fallback non attesté.

La commande `taskkill /F` interrompt directement le processus et peut interrompre des travaux en cours. Ne tester que sur service explicitement autorisé à l'arrêt et après contrôle des jobs.

## Tests

Tests statiques PHPUnit ajoutés; recette réelle sous MAIN obligatoire. Aucun service arrêté lors de la préparation.
