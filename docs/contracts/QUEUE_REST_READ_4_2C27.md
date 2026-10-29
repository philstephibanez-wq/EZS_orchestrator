# Contrat 4.2c27 : consultation REST de la queue globale

Trois GET uniquement : /api/v2/queue/jobs, /api/v2/queue/jobs/{id}, /api/v2/queue/events?after=N. Bearer obligatoire. Tokens distincts par producteur, variables de processus EZS_QUEUE_LAB_TOKEN / EZS_QUEUE_ASSISTANT_TOKEN / EZS_QUEUE_EZSCORE_TOKEN, au moins 32 caractères, hors Git. L'identité dérive exclusivement du jeton, aucune sélection arbitraire de provenance. Accès SQLite data/queue/global.sqlite en mode read-only, query_only ; aucun fichier créé par GET. Limite 100 lignes, pagination événementielle par after. Lease token et idempotency_key jamais renvoyés. Erreurs 401, 404 et 503 non bavardes, no-store.

Pas de POST, pas d'admission, claim, heartbeat REST ni SSE dans ce lot. Le registre ne contient que les jobs qui y ont réellement été enregistrés. Ne jamais inférer une file Assistant vide d'une simple absence de ligne. Aucun vrai job traité. Événements heartbeat/progress seulement à ce stade.
