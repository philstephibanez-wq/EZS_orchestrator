# Contrat canonique — Migration Queues & Jobs 4.2c0

La série 4.2b demeure référence stable ; 4.2c0 corrige le manque de portage des comportements existants vers Symfony/PHP. Aucune fonctionnalité nouvelle.

## Sources et autorités
- Orchestrator issues #1, #8, #11, #12, #15, #18 ; issue active #20 (issue #19 archivée).
- LAB : file scientifique `analysis_jobs` (handoff R3B6) et service de lease distribué ; ne pas réactiver l'ancien LabJobStore STEMS JSON.
- EZScore : AnalysisJobManager / AnalysisJobRepository conservent l'état métier.
- Assistant : file IA et exécution séparées, contrats REST à vérifier sur MAIN avant activation ; aucune référence exécutable XPS/Docker historique.
- Orchestrator : coordination, transport Symfony Messenger, arbitrage GPU et observabilité ; payload scientifique opaque.

## Parité V1 requise
- Cibles DEV, PROD, LAB distinctes et attribuées irréversiblement au claim.
- Enveloppe `ezscore.analysis-job.v2` ou adaptation explicitement versionnée ; job_id, target, kind, resource_class, priority, correlation_id/idempotency_key, provenance sans diffusion de secrets.
- `queued` visible avant claim ; attempt créé dès `running`, puis même attempt actualisé `completed`, `failed` ou `finalize_error`.
- RC analyse distinct de finalisation : worker RC=0 + callback/complete non confirmé = `finalize_error`, non `failed` ; worker RC !=0 = `failed` avec finalisation non tentée.
- Claim/lease/fencing atomiques, un seul slot GPU machine-wide et parallélisme CPU compatible ; aucun double traitement au retry ou crash/ack.
- Callback de statut/progress/complete/fail authentifié, reprises bornées, erreurs définitives distinguées des transitoires, annulation, délai et dead-letter.
- Tableau des queues, attempts et incidents en actualisation locale, sans lecture directe des BDD d'autres dépôts, sans logs d'exécution intégraux dans navigateur/export.
- Ne **jamais consommer** les jobs LAB #181/#182/#185 durant la migration ; aucune action PROD sans recette autorisée.

## Gates d'implémentation
1. Retrouver et vérifier les sources V1 historiques effacées de HEAD ; établir matrice source → comportement → test → service Symfony.
2. Migrer le minimum à comportement identique avec tests unitaires et concurrents (dont cas callback ambigu) ; pas de remplacement par une heuristique.
3. Tester l'intégration REST sur MAIN en lecture seule avant tout claim, puis tester jobs synthétiques DEV isolés ; cas PROD séparé.
4. Avant toute suppression, établir l'équivalence durable et la non-régression des scripts canoniques START/STOP v4.2b.
5. Mettre à jour issues, contrat et handoff à chaque révision ; absence de worker/queue activé pour ce commit d'ouverture.

Ce contrat n'atteste **aucune migration de queue exécutée**.
