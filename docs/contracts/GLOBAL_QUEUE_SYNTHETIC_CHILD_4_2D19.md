# 4.2d19 — Enfant PHP synthétique isolé

- Exécution **explicite**, one-shot, sans route, cron, Messenger, service ni activation PROD.
- Base SQLite **obligatoirement située sous le répertoire temporaire** ; jamais la queue canonique de production.
- Claim CPU uniquement. Seuls `producer=EZS_SYNTHETIC` et `kind=synthetic_child` sont autorisés après claim.
- Enfant réel démarré par `proc_open` avec tableau d'arguments PHP, sans shell. L'observateur externe fourni par l'appelant doit attester PID, node, created_at et instance_id. Le runner ne fabrique jamais ces attributs.
- Identité persistée via `ExecutorOwnershipRegistry` avant heartbeat. Attestation incohérente : **aucun succès**, lease laissé en cours en sécurité (fail-closed).
- Fin `completed` uniquement après sortie zéro, sortie standard exacte et sortie d'erreur vide. Échec enfant : `failed` si lease valide.
- Tests : enfant PHP réel et observation simulée ; cela ne démontre **pas** une sonde Windows indépendante. Aucune garantie contre descendance survivante, PID reuse, crash brutal, ni récupération automatique.
- Limitation : l'absence de journal `spawn_pending` atomique et d'identité du groupe interdit la récupération autonome dans ce lot. Ne pas raccorder aux jobs GPU réels.
