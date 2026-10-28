# v2.a53 — start/stop global sans paramètre

`scripts/start.ps1` et `scripts/stop.ps1` utilisent désormais `Target=all` par défaut. L'interface opérateur redevient un simple **start / stop** ; les cibles `dev` et `gateway` sont réservées au contrôle de reprise.

**Start** : demande le statut DEV au cycle historique et réutilise DEV lorsqu'il est sain ; refuse un état DEV partiel/périmé. Si DEV est absent, il le démarre avec ses garde-fous actuels. Réutilise le gateway PHP si son état PID/ports et sa réponse de protocole sont cohérents ; sinon le lance via le démarrage PHP durable déjà livré en v2.a51. Ne redémarre jamais 8501, 8511 ni 8512.

**Stop** : s'il existe un état gateway PHP, utilise uniquement l'arrêt gateway avec vérification d'ownership ; si 8510 est occupé sans état propriétaire, refuse ; arrête ensuite les processus DEV appartenant au V2, avec les anciens garde-fous. **Il n'arrête pas l'application EZScore PROD (Caddy 8501, Caddy interne 8511 et PHP 8512)**, qui est un autre périmètre et ne doit pas être arrêté implicitement par l'Orchestrator.

Les scripts historiques `v2_lifecycle.ps1` et `prod_lifecycle.ps1` restent dans le dépôt à cette étape : la cible finale de deux seuls PS1 n'est pas encore atteinte. Le gateway Python source est absent. Le PID Python obsolète dans le state PROD historique n'est ni modifié ni repris. Aucune bascule de maintenance ni vérification réelle SSO/médias par ce commit.

Recette MAIN : pull, `php tests/GlobalStartStopContractTest.php`, `php tests/GatewayPhpProdBootstrapContractTest.php`, puis exécuter `scripts/start.ps1` sans paramètre ; vérifier le protocole 8510 et l'état global. Tester `stop.ps1` **uniquement dans une fenêtre de maintenance acceptée**, car il arrête le gateway PHP et le DEV possédé. Windows 11 zéro fenêtre, auto-redémarrage et robustesse lifecycle restent à qualifier. Les tests MAIN du nouveau code ne sont pas exécutés lors de publication.
