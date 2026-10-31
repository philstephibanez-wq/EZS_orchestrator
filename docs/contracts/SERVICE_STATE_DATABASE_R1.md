# Contrat — Registre SQLite, lot 1 (préparation)

- La source active des commandes reste `desired-services.json` tant que la bascule n'est pas livrée et validée.
- La nouvelle base `runtime/supervision/service-state.sqlite` est durable sur MAIN. Jamais dans `H:\temp`.
- Import initial non destructif des cinq intentions et du mode maintenance PROD, avec un journal d'opérations.
- `prod_maintenance=ON` correspond au booléen `maintenance=true` dans le gateway canonique. Le gateway reste autorité durant le lot 1.
- Les sondes de santé ne changent jamais les intentions. Une action doit porter un acteur et un résultat confirmé.
- Cette livraison n'active ni tâches Windows, ni récupération automatique, ni commande d'arrêt/démarrage. Elle ne modifie pas la PROD.
- Phase suivante bloquée : intégration transactionnelle de tous les points d'écriture (CLI + UI + mode PROD) et traitement des conflits entre JSON, gateway et SQLite.
- Migration vérifiable et idempotente, sans suppression des fichiers JSON historiques.
