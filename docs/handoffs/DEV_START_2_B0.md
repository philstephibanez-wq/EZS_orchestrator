# v2.b0 — DEV : démarrage résistant aux états déjà actifs

## Objet
Le nouveau cycle v2.b0 stabilise la commande sans option `scripts/start.ps1` pour l'**Orchestrator DEV uniquement**. Aucun démarrage de la passerelle PHP PROD. Le contrat STOP v2.a57 reste inchangé : le STOP met PROD en maintenance vérifiée puis arrête DEV ; START ne désactive pas la maintenance.

## Changement
Le lifecycle DEV vérifie maintenant une instance déjà démarrée (PID, image/commande, port 8791, port 8790 et les façades 8502/8852 associées au même Caddy). Si l'état est sain, `start` répond `EZS_DEV_ALREADY_RUNNING_VERIFIED` sans toucher aux processus. Si l'état est périmé ou partiel, il refuse toujours le démarrage : aucun kill aveugle, aucune prise de port concurrente. Pour un état absent, le lancement nominal de PHP FastCGI/Caddy est inchangé.

## Contrôle MAIN
`git pull --ff-only origin master`
`php tests/DevStartIdempotency2B0ContractTest.php`
`powershell -ExecutionPolicy Bypass -File .\scripts\start.ps1`
`powershell -ExecutionPolicy Bypass -File .\scripts\v2_lifecycle.ps1 -Action status`

Un test d'arrêt puis de démarrage implique **l'activation de la maintenance PROD** par STOP, et n'est pas une simple recette transparente pour les visiteurs. Les tests ci-dessus n'arrêtent aucun composant.

## Limites
Cette première implémentation v2.b0 ne démarre pas d'autres services DEV externes (port 8602/8701/8702/8712/8862) dont le lifecycle/ownership n'est pas défini ici. Le contrat de suppression des scripts PS1 supplémentaires et le remplacement PHP du lifecycle restent ouverts. Aucun test Windows MAIN n'a encore été exécuté pour v2.b0.
