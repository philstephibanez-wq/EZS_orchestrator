# Orchestrator — expertise completed, rapport ciblé 1.3a(21)

Après publication du complément LAB `scripts/publish_review_event.py`, le garde `publish_completed_revision(revision_id)` de l'Orchestrator invoque uniquement ce rapport. Il refuse les brouillons, les tâches Windows actives et l'absence de l'option `EZS_EVENT_REPORTS_ENABLED=1`; les rapports existants sont dédupliqués par empreinte. Aucun watcher périodique ni nouvelle tâche n'est créée.

**Ne pas activer** : la notification métier automatique depuis `ProfileExternalReviewService::save` n'est pas encore connectée. L'activation doit intervenir après une recette avec publication simulée et neutralisation des anciennes tâches Windows ; les jobs #181/#182/#185 ne doivent pas être consommés. Aucun lancement Orchestrator ni LAB dans cette livraison.
