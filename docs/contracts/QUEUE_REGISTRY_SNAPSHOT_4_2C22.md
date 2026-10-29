# 4.2c22 — Observation réelle du registre Orchestrator

Une seule queue globale cible. La présente tranche apporte une **lecture du registre SQLite existant**, sans prétendre migrer ni reconstituer toutes les sources de jobs. Le registre 4.2c3 contient actuellement des cibles historiques dev/prod/lab et aucun producteur Assistant standard ; il ne constitue pas encore la queue globale.

Configuration opt-in : variable d'environnement `EZS_QUEUE_REGISTRY_PATH` donnant le chemin exact de la base du registre existant. Ouverture SQLite en URI `mode=ro` et `PRAGMA query_only=ON`, sans création de fichiers ni table. Aucune base inventée, pas d'insertion synchronisée depuis LAB, pas de claim, pas de dispatch, pas d'état « vide » en l'absence de source.

La page Files & Jobs distingue les jobs du registre Orchestrator de l'observation externe LAB, chacune étiquetée selon son périmètre. Étape suivante : raccordement des producteurs LAB/Assistant par une enveloppe commune et des transitions atomiques, tests de non-régression V1, avant prétention à une queue opérationnelle.
