# Contrat 4.2c19 — Interface Infrastructure et Files & Jobs

Infrastructure est l'autorité de présentation des états des services. Chaque carte DEV, PROD, LAB, Assistant contient exactement cinq rubriques de détails techniques : Façade, Backend, Autorité Orchestrator, Action, État complémentaire. États LAB et IA via sondes GET existantes ; aucun claim ni dispatch. Files & Jobs garde les jobs LAB et archives historiques, mais aucun panneau Assistant. La connectivité de la file reste indiquée brièvement près du tableau métier. Échec de sonde => état non confirmé, jamais inventé. Ne pas modifier START/STOP ni états scientifiques.

Recette exigée : test PHP de disposition, lint PHP/Twig, contrôle navigateur, job #193 intact. Aucun test runtime réalisé à la publication.

## Correction architecture 4.2c20
Une seule queue globale, gérée par Orchestrator, indépendante de la provenance et du métier du job. LAB et Assistant sont des producteurs/consommateurs indépendants, pas des queues séparées. Infrastructure n'affiche aucun compteur de jobs. Files & Jobs doit présenter la queue unique avec provenance, état, priorités et tentatives ; la sonde LAB actuelle est une vue partielle clairement identifiée jusqu'au portage du registre global.
