# Contrat 4.2c32 — Dashboard unique

La page Files & Jobs lit exclusivement `data/queue/global.sqlite` par `GlobalQueueDashboard`, via PDO `mode=ro` et `query_only`. Une seule table regroupe toutes les provenances ; progression et phase viennent des événements persistés. Pas d'appel HTTP vers LAB pour construire une pseudo-queue. Les archives historiques restent explicitement séparées.

Une queue vide signifie uniquement aucun job enregistré dans **cette base** ; elle ne prouve rien sur les anciennes files des applications. Aucun import implicite, aucun claim. Le producteur conserve l'exécution et la vérité métier. Tests sur SQLite synthétique temporaire ; base permanente non modifiée par la recette.
