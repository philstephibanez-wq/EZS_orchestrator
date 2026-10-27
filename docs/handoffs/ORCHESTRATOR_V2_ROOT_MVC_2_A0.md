# Handoff v2.a0 — unification MVC Symfony à la racine

## Décision
Symfony est **EZS_orchestrator**, et non le seul sous-répertoire `web/`. Modules MVC au root ; responsabilités génériques seulement. Gestion de queues par Symfony Messenger ; publication des résultats d'analyse/contre-expertise en one shot après terminal confirmé vers `EZStudio_Run_Reports`. Exécution des commandes externes par services PHP, sans CMD/PowerShell/Python wrappers ; exception start et sondes techniques, jamais de fenêtre console Windows 11.

## Livraison source réalisée
- Copie atomique des 37 fichiers Symfony suivis par Git sous leurs chemins root : bin, public, src, templates, config Symfony et composer.
- Correction des chemins relatifs de `ProdFastcgiPreflightCommand`, `HomeController`, `ProdOperationsController`.
- `composer.json` root déclaré `ezs/orchestrator` ; `.gitignore` protège vendor/var/.env.local root.
- Test structurel non mutateur : `tests/SymfonyRootStructureTest.php`.
- Contrat : `docs/contracts/ORCHESTRATOR_V2_ROOT_SYMFONY_MVC_2_A0.md`.

## Limites / risques non résolus
- `web/` reste intact car les services actuels l'utilisent ; aucun Caddy/proxy ni service n'a été reconfiguré.
- Dépendances Composer root non encore installées ni testées sur MAIN ; lock copié, sa cohérence avec le nom du package reste à confirmer.
- Le contrôleur PROD de maintenance historique invoque toujours Python. Ne pas exposer ni utiliser la route mutante du root jusqu'à migration sécurisée ; PROD reste en maintenance.
- Les services Windows, le worker queue Messenger, le moteur de publication événementielle et le gating anti-fenêtre console ne sont **pas** encore migrés.
- Les références legacy à `web/` et les tests historiques doivent être inventoriés avant tout retrait.

## Recette MAIN — sans action sur les services
Depuis `H:\EZS_orchestrator` :
1. `git pull --ff-only origin master`
2. `Get-Content .\VERSION` → `2.a0`
3. `$PHP = 'H:\PHP\php-8.5-x64\php.exe'`
4. `& $PHP -l .\src\Kernel.php`
5. `& $PHP .\tests\SymfonyRootStructureTest.php` → `SYMFONY_ROOT_STRUCTURE_OK`
6. `& $PHP -l .\src\Module\Infrastructure\Command\ProdFastcgiPreflightCommand.php`
7. Composer root doit être installé/contrôlé dans un lot séparé avant exécution de `bin/console` root. Ne pas réutiliser par supposition le vendor de `web/`.

## Prochain lot
Rendre le root Symfony bootable et faire les tests fonctionnels Caddy/Twig/API en lecture seule ; migrer les Controllers/Services sensibles et la supervision Windows sans console ; préparer une bascule réversible avant de supprimer `web/`. Tous les jobs existants et les services restent inchangés.
