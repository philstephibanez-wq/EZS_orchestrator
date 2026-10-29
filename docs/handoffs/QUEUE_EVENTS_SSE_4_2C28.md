# 4.2c28 — SSE par lots, sans canal permanent

Ajout de QueueEventStream et d'une route GET authentifiée `/api/v2/queue/events/stream`. Une requête renvoie jusqu'à 100 événements dans une réponse `text/event-stream`, puis termine ; `Last-Event-ID` permet de reprendre. Le caractère temps réel sera atteint par re-connexion pilotée par le client, pas par un push continu dans cette version. Pas de POST ni claim de jobs. Contrat et test synthétique. Recette Windows lints + router + 401 à faire.
