# v4.2c38 LAB/Assistant post-reboot

`lab-assistant.json` doit être nettoyé seulement si **les deux anciens processus ont disparu**, les deux ports 8701/8713 sont libres et aucune attestation complète ne réussit. Si un seul processus survit : refus. L'action status reste non destructive. Aucun changement à Caddy, PROD ou queue. Les échecs Windows START dus à l'attestation du Caddy partagé et l'état PROD non attesté demeurent ouverts et ne sont pas masqués. Validation PowerShell AST et START réel nécessaire.
