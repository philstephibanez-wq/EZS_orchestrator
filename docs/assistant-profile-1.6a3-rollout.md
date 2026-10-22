# Déploiement ciblé Assistant v1.6a(3) — 22 octobre 2026

La supervision historique cherchait l'ancien `app/main.py profile-review-auto-watch`, alors que le worker courant exécute `runtime/profile_ai_requests_worker.py`. Correctif du statut : `assistant_supervision/manager.py` identifie maintenant l'un ou l'autre chemin sans supposer que le worker distribué existe.

Livrable d'activation : `scripts/deploy-profile-v1.6a3.ps1`. Sur MAIN, la commande `powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\deploy-profile-v1.6a3.ps1` met à jour la source Assistant en fast-forward, puis met à jour XPS en fast-forward sans effacer les fichiers non suivis ; exécute les tests, compile Python, redémarre exclusivement le processus PROFILE via Guardian (singleton requis), et vérifie l'API web existante. Ne stoppe pas les serveurs LAB, les workers scientifiques, Caddy/PHP ni Guardian.

Précondition : aucune révision PROFILE active ; arret du worker pendant un job annulerait ce job. Les changements Git suivis sur MAIN/XPS provoquent l'abandon. La version attendue est `1.6a(3)`.

Critère logiciel : `V16A3_PROFILE_DEPLOY_OK`, PID renouvelé, API répondante, version correcte. **Ce n'est pas une preuve musicale**. Après le prochain run, examiner `comparison.final_verification.evidence_diagnostic` pour trouver le motif de rejet des sources. Ne pas demander de refaire des analyses scientifiques.

La supervision distribuée `distributed-watch` peut rester absente et les heartbeats périmés ; le fix du statut PROFILE ne démarre pas ce processus. Le bouton « Démarrer assistant » repose toujours sur un helper historique et ne doit pas être utilisé pour contourner l'absence de worker distribué. Git tags/releases formels non créés.
