# R7C — Hard evidence / bootstrap

Version 4.2d68. Un seul instant de collecte native par site et par commande.
Ligne de compatibilité `SITE=...` inchangée pour les lecteurs R6. L'ancien `OWNED=2` représente un état non attesté, **pas** deux PID. Ligne R7C supplémentaire `HARD_SITE=...` : `PROCESSES` est le nombre réel de processus correspondant à la signature, `PORTS` le nombre de ports distincts, `REASON` la cause d'échec et `RECORD` l'attestation du propriétaire.

Un site natif est `RUNNING` uniquement avec un exécutable/commande unique, une preuve propriétaire PID+date cohérente, les ports requis associés au bon PID et aucun port étranger. L'absence de preuve reste `UNVERIFIED`, jamais une permission d'arrêt.

La commande `HardStatus` échoue si un site normalement attendu actif n'est pas `RUNNING` ; en mode Maintenance, PROD est exclue de ce critère. Le bootstrap ne tue ni n'adopte les processus inconnus.

Risques conservés : `DEV_MEDIA_ROOT_ENV_MISSING` et la dépendance `caddy.exe` du lanceur Assistant appartiennent à des préconditions extérieures non modifiées ici ; aucune supposition de chemin et aucune modification des dépôts frères. La bascule PROD/maintenance et le ping soft restent hors R7C. L'absence d'attestation propriétaire LAB, même si HTTP fonctionne, interdit l'arrêt automatique.

Le contrat historique de persistance `desired-services.json` entre en conflit avec la décision opérateur du 2026-11-03 (boot initial automatique, commandes manuelles non persistantes, Maintenance seule persistante). La présente note décrit le comportement cible sans supprimer les fichiers historiques ni prétendre avoir migré les contrôleurs manuels.
