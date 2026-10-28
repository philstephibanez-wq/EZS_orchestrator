# Files & Jobs — Contrat v2.5a0

## Provenance vérifiée sur GitHub
Orchestrator #8 : files DEV/PROD, queued visible, running dès début, attempt unique mis à jour au final, completed/failed/finalize_error, métadonnées et colonnes, refresh local, API /api/jobs, aucun execution.log intégral. Réussite et échec DEV ainsi que sérialisation GPU validés ; validation de nouveau job PROD non acquise.
Orchestrator #15 et #18 : coordination REST Symfony/PHP 8.5, Messenger, outbox, idempotence, lease, fencing, claim atomique, retry borné, dead-letter, annulation et reprise sur crash après exécution distante avant ack. Jobs LAB 181/182/185 interdits de claim pendant migration.
LAB #16, archive R3B6 et DistributedAnalysisLeaseService.php : la table analysis_jobs est la file scientifique ; ancien LabJobStore JSON STEMS historique non réactivable ; assistant.profile.review distinct des jobs scientifiques ; heartbeat et leases domaine LAB préservés.
Assistant #5 et profile_worker_supervisor.py : singleton worker et observations IA draft/idempotentes, sans validation externe ni promotion scientifique implicite.
EZScore AnalysisJobManager.php : jobs domaine et transitions persistées propres à EZScore, aucune lecture croisée de base de données.
Orchestrator ExclusiveLease.php : verrou OS scopes control/gpu-executor, ne remplace pas une queue persistée.

## Invariants bloquants avant portage
- Orchestrator coordonne les enveloppes opaques, LAB/Assistant/EZScore gardent données métier et répertoires respectifs ; MAIN seul.
- Priorités, resource_class GPU machine-wide sérialisée, parallélisme CPU permis, claim/fencing/lease transactionnels, zéro double traitement.
- Historique attempts dès running, états et erreurs consultables, API authentifiée, journal compact sans contenu privé.
- Crash/retries/replay idempotents, outbox, ack après preuve distante, cancel et dead-letter ; Messenger seul ne garantit pas exactement-once.
- Aucune consommation des jobs LAB 181/182/185, aucun job PROD sans validation séparée.
- Aucun nouveau worker, aucun redémarrage, aucune migration DB ou changement START/STOP stable v2.4b durant v2.5a0.

## Points à vérifier dans les anciens commits
Les classes d'Orchestrator V1 ont été supprimées de HEAD : retrouver historique du dispatcher, schéma d'attempts, persistance, fairness, commandes REST et comportement des erreurs avant implémentation. Audit initial non exhaustif. Issue #19.