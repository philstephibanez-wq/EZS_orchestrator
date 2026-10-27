# Orchestrator reports-drain — CLI manuel, 1.3a(23)

LAB écrit des événements PROFILE `completed` dans `profile_report_events`. L'Orchestrator peut les traiter ponctuellement via `python -m control_center.cli reports-drain`, exclusivement avec `EZS_EVENT_REPORTS_ENABLED=1`, après arrêt des tâches publisher/watcher legacy. Chaque révision est publiée individuellement et acquittée `published` seulement après confirmation du publieur. Toute erreur laisse `pending` pour reprise ; le publieur est idempotent.

**Pas de timer, tâche planifiée, watcher ou changement scientifique.** Cette commande n'est PAS lancée automatiquement par Symfony ; l'intégration UI/événementielle directe n'est pas encore faite. Ne pas activer ni exécuter sur la base réelle avant un test sur copie isolée et décision explicite sur l'historique en attente. Conserver les jobs #181, #182 et #185.
