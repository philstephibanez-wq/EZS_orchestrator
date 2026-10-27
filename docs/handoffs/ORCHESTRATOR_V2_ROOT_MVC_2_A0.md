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


## Lot root MVC complémentaire — 27/10/2026
- `web/config/caddy/*` a été **copié** dans `config/caddy/*` sous Symfony root (ancien chemin encore préservé pour runtime V1).
- Préflight PHP root pointe maintenant vers `config/caddy/Caddyfile.prod-internal-candidate`.
- Route mutante PROD dans la copie root : fail-closed HTTP 503 `prod_lifecycle_migration_pending`, **sans** invocation Python ; ancien `web/` inchangé.
- Nouveau contrat statique : `tests/SymfonyRootRuntimeContractTest.php`.
- Composer root n'a pas encore son `vendor/` : les erreurs `autoload_runtime.php` rapportées proviennent de l'absence d'installation, pas d'une preuve d'échec Kernel.
- La supposition antérieure `H:\PHP\composer.phar` était incorrecte ; découverte de Composer avant installation obligatoire. Ne pas copier `web/vendor`.

### Commandes de recette MAIN, sans activation de services
```powershell
cd H:\EZS_orchestrator
git pull --ff-only origin master
$PHP = "H:\PHP\php-8.5-x64\php.exe"
& $PHP .\tests\SymfonyRootStructureTest.php
& $PHP .\tests\SymfonyRootRuntimeContractTest.php
$composer = Get-Command composer -ErrorAction SilentlyContinue
if (-not $composer) { throw "COMPOSER_NOT_FOUND: installer/retrouver Composer avant la suite" }
& $composer.Source validate --no-check-publish
if ($LASTEXITCODE -ne 0) { throw "COMPOSER_VALIDATE_FAILED" }
& $composer.Source install --no-interaction --prefer-dist --no-scripts
if ($LASTEXITCODE -ne 0) { throw "COMPOSER_INSTALL_FAILED" }
& $PHP .\bin\console about
& $PHP .\bin\console debug:router
& $PHP .\bin\console ezs:prod:fastcgi-preflight
```
Si `composer` est une commande `.cmd`, elle est exécutée **seulement dans la console de recette déjà ouverte**, pas dans le runtime Orchestrator. Ne pas déclencher de processus en tâche de fond ou de changement Caddy ici.

**État : code livré, recette MAIN de ce complément en attente ; aucune suppression `web/` autorisée avant bascule validée.**


## Recette MAIN root validée — 27/10/2026
- `SYMFONY_ROOT_STRUCTURE_OK` et `SYMFONY_ROOT_RUNTIME_CONTRACT_OK`.
- Composer installé sur MAIN depuis la commande détectée sur le PATH : **42 packages** et autoload généré dans le vendor racine ; `composer install --no-scripts` a terminé avec code 0.
- `bin/console about` : Symfony 7.4.21 LTS, PHP 8.5.11, Kernel `Ezs\\Web\\Kernel`, environnement `dev`.
- `bin/console debug:router` : routes MVC racine détectées (dont `/`, `/api/v2/environments`, `/api/v2/gpu/main`, `/api/v2/infrastructure/prod-control`).
- `bin/console ezs:prod:fastcgi-preflight` : maintenance true, ports 8511/8512 libres, candidate_only true.
- `composer validate` signalait un `composer.lock` non synchronisé suite au changement de nom de package `ezs/orchestrator-web` vers `ezs/orchestrator`. Correctif sur master : **mise à jour ciblée du `content-hash` Composer** (`07229fc62a5472051ff874f2b6c5cd9e`), calculée avec l'algorithme du Locker Composer et vérifiée contre le hash de l'ancien package. Aucune version de dépendance changée. Validation Composer locale après pull encore requise.
- Ne pas supprimer `web/` : Caddy/runtime V1 n'est pas encore basculé ni testé en HTTP sur le root. Ne pas activer PROD, ni traiter les jobs en attente.


## Lot HTTP/Twig racine préparé — v2.a0
- Composer validate sur MAIN confirmé : `./composer.json is valid`, lock synchronisé ; Symfony 7.4.21/PHP 8.5.11 et routes root détectées.
- Test **in-process** sans listener ajouté : `tests/SymfonyRootHttpKernelTest.php` vérifie les réponses HTTP internes GET `/` (Twig, version `2.a0`) et GET `/api/v2/environments` (JSON) à travers le Kernel Symfony racine. **Pas encore exécuté sur MAIN.**
- `HomeController` racine explicite désormais Content-Type HTML/UTF-8 et Cache-Control no-store.
- Nouveau `config/caddy/Caddyfile.orchestrator-root-preview` : candidate loopback **8890 → 8891**, docroot `H:/EZS_orchestrator/public`, admin off. Ports distincts de 8790/8791, aucune activation.
- **Gate impératif** : aucun Caddy ni PHP-CGI lancé dans ce lot ; première recette valide la configuration et le Kernel in-process. La vraie recette HTTP réseau/Windows et zéro fenêtre console reste à effectuer avant switchover. `web/` demeure opérationnel et intact.

### Recette MAIN (lecture seule vis-à-vis des services)
```powershell
cd H:\EZS_orchestrator
git pull --ff-only origin master
$PHP = "H:\PHP\php-8.5-x64\php.exe"
& $PHP .\tests\SymfonyRootHttpKernelTest.php
& $PHP .\bin\console lint:twig .\templates
& "H:\Caddy\caddy.exe" validate --config .\config\caddy\Caddyfile.orchestrator-root-preview --adapter caddyfile
```
Attendu : `SYMFONY_ROOT_HTTP_KERNEL_OK`, templates Twig valides, `Valid configuration`. Rien n'est démarré ou redirigé. Si échec du test, ne pas modifier Caddy actif, joindre le log.
