# EZS_orchestrator R3.19 — LAB cancellation

- sonde le statut du job pendant l'exécution ;
- `cancelling` => arrêt réel de l'arbre process ;
- Windows : `taskkill /T /F` ;
- callback `/cancelled` ;
- libération du singleton GPU ;
- historique = `CANCELLED`.

Redémarrer le service permanent après application, quand aucune analyse n'est active.
