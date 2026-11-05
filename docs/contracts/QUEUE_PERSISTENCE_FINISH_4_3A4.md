# Orchestrator 4.3a4 — Finalisation sous attestation de persistance LAB (porte fermée)

## Provenance et décision

Référence publiée de départ : Orchestrator `4.3a3` (`63b9feca32bc52decf5e62542616d5c2f387ce41`), LAB `1.6a2` (`06a7f16002ae5b12f26f47e4f2966b5240984215`). Contrat canonique : `CONTRAT DE DÉVELOPPEMENT.md`, SHA `6b3738a295efc99def4ebe54c55da93b290b6148`. `AGENTS.md` des deux dépôts lus.

Le noyau `GlobalQueueStore::finish()` demeure l'unique autorité pour les états techniques. Le nouveau contrôleur ne peut appeler `finish()` que si LAB a émis une attestation HMAC liant **le résultat déjà persisté** au job global, à sa référence métier et à la génération de son lease. Aucun signal `success=true` non attesté ne suffit. Aucune nouvelle queue, scheduler, lanceur scientifique ou transport concurrent n'est introduit.

## Interface dormant par défaut

`POST /api/v2/queue/executor/finish`, loopback direct seulement, `Content-Type: application/json`, limite 2048 octets, JSON objet à clés strictement définies, `Cache-Control: private, no-store`.

Authentification **executor**, distincte du jeton producteur : `EZS_QUEUE_EXECUTOR_API=1` et Bearer `EZS_QUEUE_EXECUTOR_TOKEN` (existant dans 4.3a3). Signature LAB distincte : `EZS_QUEUE_LAB_RESULT_ATTESTATION_KEY`, secret de 32 à 256 octets présent dans l'environnement natif ou Symfony du serveur Orchestrator. Aucun de ces drapeaux ou secrets n'est provisionné par ce lot, ni lu depuis `.env.local` par la nouvelle route. **L'API reste 404 par défaut.** Un secret non provisionné entraîne 503 avant ouverture SQLite.

```json
{
  "job_id": 42,
  "claim_generation": 1,
  "lease_token": "<64 hex characters>",
  "receipt": {
    "schema": "ezs.lab.persisted-result.v1",
    "producer": "lab",
    "external_id": "analysis_job:201",
    "job_id": 42,
    "claim_generation": 1,
    "result": "completed",
    "artifact_sha256": "<64 hex characters>",
    "signature": "<64 hex characters>"
  }
}
```

Pour `failed`, `artifact_sha256` est `null`. HMAC-SHA256 hexadécimal lowercase sur les **sept lignes ASCII** séparées par LF, sans LF final : `ezs.lab.persisted-result.v1`, `lab`, `external_id`, `job_id`, `claim_generation`, `result`, `artifact_sha256` ou `-`. La signature n'est produite **que par un composant LAB à développer** après validation et persistance réelles du résultat métier, ou après persistance de son échec. La clé ne doit jamais transiter en HTTP ni dans Git, ni être détenue par un client non fiable. Des tests de vecteurs de signature partagés LAB/Orchestrator sont requis avant mise en exploitation.

`422` : structure ou signature invalide ; `409` : lease/génération expirés ou déjà clôturés ; `401` : exécuteur non autorisé ; `403` : pair distant ; `503` : clé de preuve absente ou base indisponible. `200` seulement après `GlobalQueueStore::finish()` atomiquement réussi. Réponses sans token ni donnée musicale.

## Étude d'impact avant/après

| Composant | Avant | Après | Risque / prévention | Restauration |
|---|---|---|---|---|
| Queue SQLite globale | `finish()` interne seulement | même `finish()` appelé après attestation | Aucune migration ni changement de schéma ; tests SQLite jetable ; API fermée | Désactiver `EZS_QUEUE_EXECUTOR_API`, puis rollback du code avant activation |
| Identité d'exécuteur | claim/heartbeat par Bearer dédié | finish par **le même** Bearer | Double autorité évitée par génération, token, expiration et vérification répétée dans `finish()` | Retirer uniquement le contrôleur dormant |
| Preuve métier LAB | aucune | format strict de reçu signé | Un reçu faux ou périmé refuse l'opération ; aucune finalisation sans émetteur LAB opérationnel | Rien à migrer |
| LAB/PROFILE | `dispatch_owner=orchestrator` interdit aux workers legacy | inchangé | Aucune modification LAB, données, moteur, UI, jobs #181–198/#201 | Sans objet |
| Windows/FrankenPHP/PROD | aucun déploiement de service | aucun redémarrage, aucune activation | Pas de nouvelle tâche, port, processus ou cache touché | Rollback uniquement fichiers sous Orchestrator |

## Bloqueurs explicites

1. LAB ne possède pas encore le protocole de transition autorisée de `analysis_jobs` ni l'émetteur HMAC de résultat persisté. **Un simple fichier `profile.json` ne vaut pas persistance métier.** Le déclencheur `trg_global_queue_admission_fence_status` doit rester actif.
2. Il n'existe pas de lanceur attesté ni d'inventaire des descendants. `claim`/heartbeat/finish HTTP ne constituent pas un worker.
3. Une éventuelle reprise d'un `finish` dont la réponse réseau est perdue devra utiliser une preuve LAB persistée et un rapprochement idempotent ; le store actuel supprime le token après clôture. Cette livraison ne prétend pas fournir ce rapprochement.
4. Activer `EZS_QUEUE_EXECUTOR_API`, `EZSTUDIO_GLOBAL_QUEUE_ADMISSION` ou consommer #201 reste interdit tant que le protocole LAB, l'exécuteur et la recette isolée ne sont pas validés.

## Recette

Environnement disponible hors MAIN : contrôle PHP `php -l`, tests directs de `QueueResultReceipt` sans réseau/SQLite, intégrité du ZIP, UTF-8 sans BOM et simulation préflight/apply/rollback sur dépôt Git fictif. Sur MAIN : tests PHPUnit ciblés, suite complète, `lint:container`, `debug:router`, `git diff --check`, `lint:twig` si nécessaire, vérification HTTP **sans jeton** du 404 désactivé pour `/finish`. Ne jamais envoyer de requête de finish/claim authentifiée à MAIN pendant cette recette. Vérifier que les snapshots LAB et le nombre des jobs globaux sont inchangés.
