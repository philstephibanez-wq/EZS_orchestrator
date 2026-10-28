# v2.a45 — confrontation des identités DEV (lecture seule)

Le service pur `DevOwnershipAssessment` rapproche le fichier d'état historique DEV de deux **instantanés** de la sonde Win32 expérimentale. Il vérifie PID distincts, ports 8791/8790, noms d'exécutables attendus, chemin absolu, horodatage de création non nul et schéma des preuves. Son test rejette PID, port, image et horodatage incohérents.

Il ne démarre ni ne supprime aucun processus et n'exécute aucun binaire. Aucun service, job, Caddy ou configuration PROD n'est modifié.

**Important :** un instantané cohérent ne démontre ni la provenance authentifiée du résultat ni l'ownership atomique à l'instant de l'action. La sonde C++ v2.a43 n'a pas été compilée ni qualifiée sur Windows 11, ne prouve pas la ligne de commande et n'établit pas l'absence de console. Toutes les décisions `lifecycle_authorized` et `safe_to_cutover` restent donc à `false`. Ce module ne doit pas être branché sur une commande start/stop/repair.

Recette MAIN : `php -l src/Module/Infrastructure/DevOwnershipAssessment.php`, `php tests/DevOwnershipAssessmentContractTest.php`, ainsi que les deux tests de non-régression `DevLifecycleReadOnlyContractTest.php` et `WindowsNativeAttestationContractTest.php`. Résultats à enregistrer après exécution, pas avant.

Contrats de référence : `AGENTS.md`, issue #18, contrat MVC root et handoffs v2.a43/v2.a44. Étape suivante : mécanisme de sonde native sans console et preuve forte de l'identité avant toute migration mutante et purge PS1.
