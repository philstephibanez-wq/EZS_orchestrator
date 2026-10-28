# v2.a43 — attestation Windows native : code source exploratoire

Statut : **SOURCE SEULEMENT**, non activé et non déployable en l'état. Le composant natif C++ propose un instantané en lecture seule : socket d'écoute loopback IPv4, PID, chemin de l'image et date de création via API Win32. La classe Symfony/PHP valide un résultat structuré sans lancer de processus.

**Limites bloquantes** : absence d'attestation de ligne de commande ; absence de preuve de continuité atomique PID/port ; absence de compilation Windows MAIN ; absence de vérification zéro flash console Windows 11. Aucune commande de lancement, aucun binaire suivi, aucune configuration PROD changée. Le résultat conserve `safe_to_cutover=false` et `lifecycle_authorized=false`.

**Recette statique MAIN** : `php -l src/Module/Infrastructure/WindowsNativeAttestation.php`, `php tests/WindowsNativeAttestationContractTest.php`, `php tests/GatewayMonitorContractTest.php`. Ne pas essayer de compiler ou exécuter automatiquement la sonde sur PROD. La cible définitive devra satisfaire le critère zéro console et une identité complète vérifiée, idéalement via interface native in-process, avant raccordement au lifecycle Symfony.

Contrats : `AGENTS.md`, issue #18, `docs/contracts/ORCHESTRATOR_V2_ROOT_SYMFONY_MVC_2_A0.md`. Aucun test Windows ni de fonctionnement natif n'est déclaré réalisé. Aucun service ni queue, modèle, preset ou donnée métier touchés.
