# EZS Orchestrator — 4.2b STABLE

Date : 28 octobre 2026.

## Décision
Le mainteneur confirme que START et STOP de l'Orchestrator fonctionnent sur MAIN après la consolidation 4.2b15 et demande de promouvoir la série en **4.2b**, version stable sans compteur. Aucun changement fonctionnel n'est autorisé dans cette promotion.

## Preuves MAIN
- `git pull --ff-only origin master` vers 4.2b15 : fast-forward réussi, arbre propre avant pull.
- `php tests/OnlyStartStopPowershell42B15ContractTest.php` : OK.
- Parseur PowerShell : `SYNTAX_OK` pour `scripts/start.ps1` et `scripts/stop.ps1`.
- Retour utilisateur : START/STOP exécutés et **OK**.
- Arbre Git : seulement deux fichiers `.ps1` suivis, tous deux dans `scripts/`.

## Portée / limites
La stabilité couvre les lanceurs et la consolidation, dans le périmètre START/STOP réellement testé. La validation ne s'étend pas aux actions PROD autonomes `-ProdAction`, ni à l'ancien chat IA sur 18720, ni à l'intégralité des queues et de la migration Symfony (#18). Port 8713 Assistant présent ; absence d'écoute sur 18713/18720 constatée, sans preuve de régression imputable à Orchestrator. Le mainteneur interdit une modification de l'Assistant pour ce constat.

## Trace
Dernière révision testée : 4.2b15, commit `bf6ce53c05a3b95c17cb4db7e96b101c183595ad`.
Promotion stable : `VERSION=4.2b`, modification documentaire et adaptation du test de garde uniquement. Aucun runtime touché.
