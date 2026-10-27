# EZS_orchestrator v2.a0 — application Symfony MVC unique à la racine

Décision et premier lot d'implémentation : 27/10/2026. **Cible : une application Symfony au root, pas une sous-application web.**

## Arborescence contractuelle
- `bin/console`, `public/index.php`, `config/`, `src/Kernel.php`, `src/Module/`, `templates/`, `composer.json`, `composer.lock`, `tests/`, `var/` à la racine.
- `src/Module/<Domaine>/Controller` : HTTP et REST minces, contrôle d'accès et validation.
- `src/Module/<Domaine>/Service|Entity|Repository` : orchestration et persistance, responsabilités de modèle.
- `templates/<domaine>` : vues Twig ; `Message` et `MessageHandler` pour Messenger.
- Les commandes système, Git inclus, sont dans des services PHP ; les queues sont possédées par Messenger. Aucun traitement métier scientifique dans l'orchestrateur.
- Exception au 100% PHP interne : bootstrap initial `start` et sondes natives ; aucune fenêtre console visible, même brièvement, sous Windows 11.

## Implémentation progressive
Le premier lot **copie** au root les éléments Symfony de `web/` (src, public, bin, config Symfony, templates, composer). Les configurations Python historiques sous `config/` sont préservées, ainsi que les tests historiques sous `tests/`. Les chemins relatifs des contrôleurs et de la commande préflight ont été adaptés au root, et le nom du package est `ezs/orchestrator`.

`web/` demeure provisoirement le chemin exécuté par le système actuel. Aucun routage Caddy, aucun processus, aucun port, aucune file, aucun déploiement n'a été basculé. **La présence de deux arbres sources est transitoire et ne constitue pas deux applications actives** ; ne pas maintenir les deux après recette et bascule. L'objectif est la suppression physique de `web/` et des modules Python une fois leurs remplacements opérationnels et prouvés.

## Gates avant bascule
1. Installer les dépendances Composer **au root**, sans perturber le vendor de `web/`; vérifier la cohérence composer.lock.
2. `php -l src/Kernel.php`, `php tests/SymfonyRootStructureTest.php` et `php bin/console about`, `php bin/console debug:router`, `php bin/console ezs:prod:fastcgi-preflight`.
3. Auditer et remplacer les références résiduelles à `web/` dans le runtime, Caddy, scripts et tests ; maintenir la maintenance PROD.
4. Tests HTTP REST + Twig, sécurité, statiques, ownership PID, auth, Caddy, gestion des erreurs ; recette Windows 11 sans flash console.
5. Basculer de manière contrôlée les chemins actifs vers Symfony root, rollback garanti ; supprimer les sources `web/` doublons **dans le lot de bascule prouvée**, jamais avant.

## Statut de preuve
Les fichiers sont versionnés sur GitHub ; **les tests Windows au root ne sont pas encore exécutés**. Le contrat ne prétend pas que la migration des queues, des incidents, de la supervision ou de Python soit finie.

## Complément implémenté — root Caddy / sécurité (27/10/2026)
Les six Caddyfiles versionnés ont été copiés dans `config/caddy/` à la racine ; l'ancien chemin `web/config/caddy/` reste utilisable par les services encore actifs. Le préflight PHP racine utilise désormais le nouveau chemin. Le contrôleur de maintenance PROD de la copie racine ne doit plus exécuter Python : réponse HTTP 503 `prod_lifecycle_migration_pending` en attendant un lifecycle Symfony natif authentifié et testé. Contrat statique `tests/SymfonyRootRuntimeContractTest.php`. Composer doit être découvert sur MAIN, pas supposé à `H:\PHP\composer.phar`; installation root de vendor avec scripts désactivés au premier essai, puis tests Symfony. **Pas de bascule Caddy ni suppression `web/` dans ce lot**.
