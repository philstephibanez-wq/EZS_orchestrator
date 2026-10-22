# Rapprochement Assistant MAIN/XPS — v1.6a(2)

Constat 2026-10-22 : l'orchestrateur compare H:\EZStudioLab_assistant (source locale encore 1.5a) à XPS C:\EZStudioLab_assistant (v1.6a(1)). Le déployeur historique est volontairement désactivé avec r27_profile_safe_handover_not_implemented. Le statut UPDATE_AVAILABLE ne prouve donc pas que XPS est en retard.

Livrable : scripts/reconcile-assistant-v1.6a2.ps1, compatible Windows PowerShell 5.1, deux modes :
- Lecture seule (défaut) : versions et état MAIN/XPS, PID du worker PROFILE.
- -Apply : vérifie la propreté des Git, met à jour MAIN source et XPS en fast-forward, valide le test du nouveau statut PROFILE, compile Python, redémarre seulement le serveur web XPS par les scripts de cycle de vie existants, puis lit /api/status.

Commande MAIN :
```powershell
Set-Location H:\EZS_orchestrator
git pull --ff-only origin master
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\reconcile-assistant-v1.6a2.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\reconcile-assistant-v1.6a2.ps1 -Apply
```

Le script n'utilise ni l'ancien deploy() destructeur, ni l'arrêt du worker scientifique, ni l'arrêt de Guardian. Le contrôle d'authentification SSH préexistant doit fonctionner. Le nombre de workers supervisés/heartbeats reste à auditer séparément ; ne jamais faire passer 0 worker en ligne pour une réussite du pipeline.

Statut : script publié, non exécuté sur les machines ; pas de prétention de recette réussie.
