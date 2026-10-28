# 4.2c10 — Première connexion réelle LAB en lecture seule

Source GitHub LAB : `AnalysisDesktopController::queue()` route `GET /internal/analysis/desktop/jobs/queue`, auth `LabAnalysisTokenGuard` par en-tête `X-EZScore-Analysis-Token`, réponse `ezstudio.analysis-desktop.v1` avec `jobs`. La route `POST /jobs/claim` est distincte et **interdite** à ce stade.

Source Orchestrator : lecture de `EZS_LAB_ANALYSIS_TOKEN` dans l'environnement de processus, pas dans le code ou les logs. La vue /jobs appelle uniquement l'endpoint GET sur 127.0.0.1:8701 avec timeout 2 secondes, sans redirection, accepte une liste bornée à 100 éléments et n'affiche pas les champs sensibles/payloads. Si jeton absent ou réponse invalide : état « Non connectée », aucun fallback de sécurité ni fausse file vide. Les snapshots historiques restent distincts.

**Important :** le jeton d'analyse LAB doit être mis à disposition de l'environnement de processus Orchestrator sous `EZS_LAB_ANALYSIS_TOKEN` par la configuration locale sécurisée existante ; aucun secret n'est copié dans Git. Aucun redémarrage automatique. Aucun accès XPS/Docker, aucune consommation #181/#182/#185, aucun dispatch IA ni callback.

**Validation** : test de contrat avec faux transport sans accès HTTP réel ; recette HTTP MAIN requise pour confirmer la connexion authentifiée, le format de `analysisQueue()`, et le délai d'affichage. Sans secret runtime, la nouvelle carte affiche honnêtement « Non connectée ». DEV/PROD en direct restent non raccordés.
