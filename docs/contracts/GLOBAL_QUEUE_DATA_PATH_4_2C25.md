# Contrat 4.2c25 — Stockage persistant de la queue globale

Chemin canonique sous Orchestrator : `data/queue/global.sqlite` (sur le poste connu : `H:\EZS_orchestrator\data\queue\global.sqlite`). Les fichiers SQLite `global.sqlite-wal` et `global.sqlite-shm` sont dans le même répertoire. Le dossier `data/queue/` est ignoré par Git ; l'intégrité et la sauvegarde de la base appartiennent à l'exploitant.

`GlobalQueueLocation::path()` fournit le chemin sans créer de fichier. `GlobalQueueStore` continue d'accepter un chemin explicite pour les tests isolés, et crée son répertoire à l'ouverture. Ne pas initialiser la base de production automatiquement par l'affichage, les tests ou le démarrage existant. Le branchement effectif d'une admission/claim via ce chemin reste une étape ultérieure.

Aucune suppression/migration des bases historiques, aucun job existant consommé. Tests de queue continuent d'utiliser exclusivement les fichiers temporaires hors dépôt.
