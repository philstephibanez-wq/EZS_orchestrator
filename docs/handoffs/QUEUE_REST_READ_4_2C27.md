# Handoff 4.2c27

QueueRestAccess : authentification par token spécifique de producteur, protection contre les collisions ; QueueRestReadModel : PDO SQLite en lecture seule, isolation et curseur ; QueueReadController : trois routes GET sécurisées. Test isolé en SQLite temporaire. Aucune modification de START/STOP ou des files réelles. Prochaines tranches : provisionner secrets de façon sécurisée, authentifier en HTTP réel, event terminal, progression REST worker, SSE. Tests Windows, debug:router et requête 401 à exécuter avant toute exposition externe.
