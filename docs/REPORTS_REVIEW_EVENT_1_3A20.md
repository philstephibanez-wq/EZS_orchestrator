# Orchestrator 1.3a(20) — garde de publication des expertises finalisées

Analyse du contrat réel LAB : `ProfileExternalReviewService::save` accepte `draft` et `completed`; la révision est persistée dans `profile_external_revisions`. Le publieur de rapports actuel parcourt toute la base, et son watcher `--once` n'est **pas** une publication ciblée ; l'utiliser sur le simple événement de finalisation pourrait republier un historique important.

Ce correctif ajoute `reports_review_event.publish_completed_revision` : vérification read-only du statut terminé et du run PROFILE, refus si tâches planifiées encore actives, activation explicite requise. **Aucune publication réelle avant ajout d'une sélection unique de rapport dans le publieur LAB et du signal de fin d'expertise.** Les tests actuels couvrent uniquement les gardes et ne prouvent pas le workflow complet.

Ne pas activer `EZS_EVENT_REPORTS_ENABLED` pour le moment. Les jobs #181/#182/#185 demeurent intacts. Aucun service ni tâche planifiée supprimé.
