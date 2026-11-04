# Orchestrator 4.3a0 — Admission REST LAB et cartes EZScore compactes

## Autorités et périmètre

- LAB stable `1.5a` conserve `analysis_jobs` et les résultats scientifiques.
- Orchestrator `4.3a0` ajoute uniquement `POST /api/v2/queue/jobs` à l'API de lecture existante.
- Une requête est une **enveloppe technique** (pas d'audio, modèle, source, secret, résultat, preset ou payload scientifique) : `external_id`, `idempotency_key`, `kind`, `resource_class` (`cpu` / `gpu`), `priority` (entier 0–100).
- Le producteur `lab` est déduit du Bearer existant `EZS_QUEUE_LAB_TOKEN` (longueur >=32) ; l'endpoint impose aussi un pair réseau `127.0.0.1` ou `::1`. Il n'accepte pas de champ `producer` client.
- JSON strict, 8192 octets maximum, pas de redirection. La réponse `ezs.queue.admission.v1` renvoie l'identité et l'état non sensibles, jamais le token de lease ou la clé d'idempotence.
- Le code réutilise `GlobalQueueStore::enqueue` et son `BEGIN IMMEDIATE`, son unicité et son contrôle de collision. Rejouer l'enveloppe identique retrouve le même job. Une collision renvoie 409.
- Codes : 200 admis/rejoué, 401 identité incorrecte, 403 non loopback, 413 trop grand, 415 format incorrect, 422 enveloppe incorrecte, 409 collision, 503 stockage indisponible.

## Limites explicites

- Aucune route de claim, callback, dispatch, heartbeat ou consommation n'est activée par cette livraison.
- `config/packages/messenger.yaml` reste sans transport/routing/consumer ; aucune exécution sur admission.
- LAB ne publie pas encore de requêtes sur cette route : intégration LAB et finalisation métier = lots futurs distincts.
- Les jobs LAB existants (dont #181/#182/#185 protégés et #193–#197) restent **dans LAB** ; aucune migration ni import implicite.
- Une première requête POST valide sur MAIN initialisera ou modifiera `data/queue/global.sqlite` : test E2E **interdit sur la base MAIN** avant autorisation explicite. Les tests automatisés utilisent SQLite sous temp système.

## Interface DEV / PROD

- La page Infrastructure conserve tous les IDs, liens, panneaux maintenance, protections et scripts JS.
- DEV et PROD ont la même densité, des résumés identiques et leurs détails techniques repliés par défaut. La bannière PROD reste visible quand active ; elle n'est jamais remplacée par l'état HTTP.
- Nouveau CSS page-local versionné ; aucune action sur service, process, Caddy, ports ou état métier.

## Étude d'impact et rollback

| Avant | Après | Risque | Prévention / recette | Rollback |
|---|---|---|---|---|
| Queue GET seule | POST admission locale / Bearer | admission indue | pair TCP direct + auth + schéma strict + test 401/403/422 ; aucune ouverture extérieure | restaurer fichiers, VERSION |
| 0 jobs Orchestrator en MAIN | 0 toujours après installation | écritures inattendues | aucun POST pendant install/recette, aucun worker | aucun changement SQLite attendu ; ne pas effacer la DB |
| DEV/PROD détails ouverts et espacés | détails repliés, résumé compact | régression de modes | IDs/JS inchangés, recette visuelle des modes normal/maintenance | restaurer Twig + CSS |
| LAB `analysis_jobs` autonome | inchangé | double consommation | pas de worker Messenger ni claim | sans objet |

## Recette MAIN

Préflight compare la version et les empreintes Git des fichiers modifiés, protège le dépôt et les changements non publiés. Apply sauvegarde les sources existantes sous `H:\temp`, valide la syntaxe PHP, les tests ciblés, l'UTF-8 sans BOM, et n'effectue **aucun HTTP POST**. La suite PHPUnit complète, `lint:twig`, `lint:container` et la recette visuelle sont à faire séparément avant publication. Vérifier la queue globale inchangée avant/après.
