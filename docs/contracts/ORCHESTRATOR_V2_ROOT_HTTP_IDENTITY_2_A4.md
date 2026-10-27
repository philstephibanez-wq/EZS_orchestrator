# Contrat de recette HTTP Symfony root — v2.a4

## Motif
Une simple réponse HTTP 200 contenant « EZS Orchestrator » ne démontre pas que le service est Symfony V2 : une interface historique peut partager ce titre. La recette de preview doit identifier le backend et l'état réel de migration, sans accepter un faux positif.

## Contrôle obligatoire
La sonde durable `tests/SymfonyRootPreviewProbeTest.php` cible uniquement la preview isolée `127.0.0.1:8890` configurée vers `H:/EZS_orchestrator/public` et FastCGI `127.0.0.1:8891`. Elle contrôle :
1. `GET /` → 200 HTML, marqueur de la vue historique Twig et titre ;
2. `GET /api/status` → 200 JSON, `source=symfony_root`, `schema=ezs.orchestrator.v2.readonly.v1`, `migration=in_progress` ;
3. `GET /api/jobs` → 503 JSON, `error=jobs_migration_pending`, `ok=false` (pas de faux état de queue).

La sonde ne démarre ni n'arrête aucun processus ; si la preview n'écoute pas, elle sort avec `ROOT_PREVIEW_NOT_RUNNING` et code 2. Un test de recette HTTP n'est pas un lanceur et n'autorise pas à faire fonctionner `php -S`.

## Limites et gate de suppression
Ce test établit seulement l'identité de la façade HTTP Symfony en cas de preview explicitement démarrée. Il n'établit ni l'équivalence des API, ni les queues Messenger, ni l'ownership PID, ni l'absence de flash de console. `web/` et les Caddyfiles actifs restent inchangés. Le retrait de `web/` est interdit jusqu'à validation fonctionnelle complète et rollback.

## Validation
Syntaxe PHP et assertions vérifiables localement ; la recette réseau MAIN et les tests Windows restent à exécuter. Aucun service n'est activé par cette livraison.
