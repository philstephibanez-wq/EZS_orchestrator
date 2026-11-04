# 4.3a2 — Jeton LAB local : résolution sans redémarrage

## Cause
Le service Windows partagé FrankenPHP ne publie pas `EZS_QUEUE_LAB_TOKEN` dans `getenv()` / `$_SERVER` / `$_ENV`. Le `.env.local` Orchestrator est provisionné, mais `symfony/dotenv` n'est pas une dépendance explicite du projet. L'API d'admission retourne donc 401 avec le secret pourtant présent sur disque.

## Correction
`QueueRestAccess` conserve l'ordre de priorité du jeton déjà injecté par le processus (getenv, $_SERVER, $_ENV). **Uniquement** pour le producteur LAB et en l'absence d'une valeur injectée, il lit à chaque requête la déclaration `EZS_QUEUE_LAB_TOKEN` dans le `.env.local` local d'Orchestrator. Une clé dupliquée, absente, malformée ou un lien symbolique fait échouer l'authentification sans exception exposant le secret. Aucun `putenv()`, aucune journalisation ni import global de la configuration.

## Étude d'impact
- Avant : 401 avec jeton provisionné mais non exporté ; après : 422 pour une enveloppe `{}` munie du Bearer LAB si le correctif est bien chargé par FrankenPHP.
- Isolation : aucune lecture de `.env.local` LAB, DEV, Assistant, PROD. Les tokens Assistant et EZScore ne changent pas.
- Processus : aucun redémarrage, aucun Caddy, WinSW, tâche Windows ni configuration de service modifiés. Le chargement du nouveau code par le serveur doit être attesté par le test HTTP.
- Queue : un POST `{}` ne crée pas de job ; les 9 anciens jobs LAB sont hors périmètre.
- Rollback : restauration du PHP et du VERSION depuis le backup sous `H:\temp`, seulement si les fichiers cible sont toujours identiques au lot appliqué.

## Recette
Tests unitaires nouveaux + suite PHPUnit complète + `lint:container`, UTF-8 sans BOM, `git diff --check`; HTTP 401 sans Bearer et HTTP 422 avec Bearer sur `{}` sans admission valide. Ne pas activer la queue et ne pas faire de POST valide. Tests MAIN à exécuter après installation. Publication Git par le mainteneur.
