# v2.a49 — réconciliation des protections après les purges v2.a46–48

**Incident :** v2.a46 a supprimé à tort les lanceurs DEV malgré l'exigence de les préserver. v2.a48 les a restaurés. `tests/LegacyPowershellPurgeContractTest.php` gardait pourtant une assertion inverse et échouait désormais sur une installation correcte.

**Correctif :** remplacer ce contrat par une assertion positive de présence de start/stop/repair/status et de leur moteur commun ; conserver l'interdiction de tout start/stop Symfony non attesté. Clarifier `POWERSHELL_BOUNDARY_V2.md` pour rendre les exceptions et le gate de bascule explicites. Aucun changement d'exécution ni suppression de scripts.

**Blocage fonctionnel restant :** le PROD actif utilise encore le gateway Python :8510 et `scripts/prod_lifecycle.ps1`. Le candidat PHP FastCGI n'est pas encore la passerelle active, faute de recette complète SSO/médias/rollback sur MAIN et d'un superviseur PHP permanent. Les commandes start/stop/repair doivent rester opérationnelles jusqu'à équivalence.

**Validation non exécutée sur MAIN :** `php tests/LegacyPowershellPurgeContractTest.php`, `php tests/LegacyLauncherPurge2A47ContractTest.php`, `php tests/DevLifecycleReadOnlyContractTest.php`, `git diff --check`. Aucune bascule ni action destructive dans ce lot.
