# v2.a44 — frontière Symfony du lifecycle DEV (sans mutation)

## Portée publiée

Le service durable `src/Module/Infrastructure/DevLifecycle.php` porte les constantes de topologie DEV du script historique `scripts/v2_lifecycle.ps1` et la lecture de son état de processus. Il fournit une décision explicite **fail-closed** pour `start`, `stop` et `repair`. Aucun lanceur nouveau, tâche Windows, wrapper PS/CMD/Python, processus, port ou service n'est exécuté/modifié.

## Inventaire contractuel à remplacer avant retrait des .ps1

- `start` : lock exclusif, refus état persistant ou ports occupés, contrôle dépendances, validation Caddy, lancement PHP-CGI et Caddy sans console, suivi du PID et rollback borné.
- `status` : état et identité réelle des processus (chemin complet, commande, date de création, port).
- `stop` : appartenance vérifiée, garde-fous façades 8502/8852 et ports 8602/8701/8702/8712/8862, arrêt **uniquement** des enfants réellement possédés.
- `repair` : Caddy strictement identifié, PHP absent, port 8791 libre, redémarrage sans toucher aux autres composants.

Le code V2 actuel **n'est pas** équivalent. `scripts/v2_lifecycle.ps1`, `scripts/start.ps1` et `scripts/stop.ps1` restent conservés pour audit ; ne pas les exécuter en remplacement du nouveau service. Aucun composant historique n'est éteint ou relancé.

## Validation

Test non destructif à exécuter sur MAIN : `php -l src/Module/Infrastructure/DevLifecycle.php` et `php tests/DevLifecycleReadOnlyContractTest.php`. Le test utilise un répertoire temporaire système et ne modifie pas les états de DEV/PROD. Seul un test local confirmé prouvera le fonctionnement sur MAIN.

**Interdictions maintenues** : aucun start/stop/repair réel ; `lifecycle_authorized=false`, `safe_to_cutover=false`. La sonde native v2.a43 ne certifie pas la ligne de commande, le lancement sans console ni l'ownership. Windows 11, rollback, queue, SSO/médias et parité Symfony restent à valider.

Références : `AGENTS.md`, `docs/contracts/ORCHESTRATOR_V2_ROOT_SYMFONY_MVC_2_A0.md`, issue #18.
