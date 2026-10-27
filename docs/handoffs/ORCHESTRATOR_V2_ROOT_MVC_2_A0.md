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


## Recette MAIN confirmée — HTTP in-process et Caddy statique (27/10/2026)
- `SYMFONY_ROOT_HTTP_KERNEL_OK`.
- `bin/console lint:twig templates` : 2 fichiers Twig valides.
- `caddy validate --config config/caddy/Caddyfile.orchestrator-root-preview --adapter caddyfile` : `Valid configuration`. Avertissement de formatage non bloquant.
- **Aucun listener preview lancé ni chaîne FastCGI réelle validée** par ces contrôles. Ne pas présenter la bascule HTTP comme terminée.
- Ajout du test PHP en lecture seule `tests/SymfonyRootPreviewProbeTest.php`. Il ne lance rien, refuse l'absence de port 8890 avec `ROOT_PREVIEW_NOT_RUNNING`, et contrôle les réponses HTTP 200 HTML et JSON si un preview a été démarré séparément et explicitement.
- Prochain gate avant activation isolée : une méthode de lancement Windows réellement sans fenêtre console, avec propriété PID stricte et rollback, et une recette manuelle autorisée sur 8890/8891. Ne pas démarrer les services par simple installation ou pull.


## Décision accueil réel et suppression de tous les .py (27/10/2026)
L'utilisateur refuse la preview 8890 et demande l'accueil historique réel tel qu'il était, au point d'entrée habituel. La référence complète est `control_center/web.py` (serveur 8700), et non la page partielle Symfony 8790. Vue historique HTML/CSS/JS transcrite fidèlement en `templates/infrastructure/legacy_home.html.twig` ; les placeholders de version sont des variables Twig, le jeton d'action historique est neutralisé. Test structurel `tests/SymfonyHistoricHomeParityTest.php`. **Vue seulement** : la route `/` Symfony existante n'a pas été rebranchée vers ce Twig faute de parité API ; aucune action sensible activée.
Contrat bloquant `docs/contracts/ORCHESTRATOR_V2_HOME_PARITY_2_A0.md`. Livraison finale : zéro `.py` dans Git, zéro invocation de Python depuis orchestrateur ; migration des actions, API, jobs, logs, supervision et états en services Symfony avant suppression. Ne pas supprimer des garde-fous encore actifs pour atteindre prématurément le compteur zéro. Pas de modification des processus, des jobs ni des ports.
Recette MAIN : `git pull --ff-only origin master`, `$PHP='H:\PHP\php-8.5-x64\php.exe'`, `& $PHP .\tests\SymfonyHistoricHomeParityTest.php`, `& $PHP .\bin\console lint:twig .\templates`.


## RAZ Python actée — 27/10/2026
À la demande expresse du mainteneur, **167 fichiers `.py` ont été supprimés de l'arbre Git de `master`**, commit `04a97245702f0825422ca7e1cb780f6edca67e63`. Source sauvegardée **dans l'historique Git** : commit parent `4b87f43a1b4a8293ee77421a007cfcc532ac2ebd`, récupérable avec `git show <sha>:<chemin>`. Aucun répertoire `backup/` permanent ne contient du Python dans le dépôt Symfony actif. Aucun cache Python versionné n'était présent dans l'arbre Git vérifié.
**Rupture voulue :** le runtime historique Python (port 8700, actions, supervision, queues, déploiements) ainsi que ses scripts de lancement anciens peuvent cesser de fonctionner au prochain redémarrage. Ne pas les exécuter, ne pas redémarrer PROD/LAB/Assistant et ne pas consommer les jobs tant que les services Symfony ne sont pas réécrits. `scripts/start.cmd` et d'autres scripts non-Python peuvent encore appeler les chemins supprimés ; ils doivent être réécrits/neutralisés dans les lots suivants. Cette suppression n'est PAS une certification de parité fonctionnelle.
### Nettoyage des caches non suivis sur MAIN
Après `git pull --ff-only origin master`, les caches locaux **non suivis** doivent être inspectés puis effacés sans supprimer les dossiers de données, les virtualenv ou les services. Commandes de recette données séparément à l'opérateur ; aucune suppression de fichiers locaux effectuée à distance.


## Lot fonctionnel accueil historique Symfony — 27/10/2026
`HomeController` racine rend maintenant `templates/infrastructure/legacy_home.html.twig` (HTML/CSS/JS historique à navigation latérale) à `/`, au lieu du tableau Bootstrap transitoire. Placeholder des versions autres projets : `—` en attendant sources fiables. **Pas de bascule de port ni redémarrage** : le Caddy actuel peut toujours servir `web/` sur 8790 et le vieux centre de contrôle 8700 n'est pas remplacé.
`LegacyReadOnlyController` expose `/api/status` avec une télémétrie TCP locale identifiée comme incomplète, et `/api/jobs` retourne explicitement HTTP 503 `jobs_migration_pending` : aucun job fictif ni consommation. Les actions d'administration, déploiement et supervision sont volontairement absentes en V2 tant que leurs services ne sont pas réécrits. Le JS historique s'affiche mais la plupart de ses requêtes/API ne fonctionneront pas encore ; **ne pas prétendre à une parité complète**.
Test `tests/SymfonyHistoricHomeRuntimeTest.php` : in-process GET `/` (visuel historique), GET `/api/status` (200) et GET `/api/jobs` (503) ; aucun listener créé. À faire sur MAIN : `git pull --ff-only origin master`, puis `& 'H:\PHP\php-8.5-x64\php.exe' .\tests\SymfonyHistoricHomeRuntimeTest.php`, `& 'H:\PHP\php-8.5-x64\php.exe' .\bin\console lint:twig .\templates`. Aucun service PROD/DEV/LAB/Assistant ni job touché.

## v2.a1 — régularisation de version sur master
Commit atomique : `VERSION=2.a1`, test `SymfonyRootHttpKernelTest.php` rendu indépendant du numéro figé, contrat et handoff mis à jour. Cette correction **ne requalifie pas rétroactivement** les commits historiques non conformes. Tests PHP et Git Windows à exécuter sur MAIN ; aucun service démarré. Modifications locales `git rm -r web` et copies des tests encore chez le mainteneur : ne pas les écraser ; les intégrer après synchronisation, puis leur donner une nouvelle révision (par exemple `2.a2`) lors de leur commit cohérent.
