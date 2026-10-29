# Contrat canonique — Queue unique Orchestrator 4.2c20

## Invariant
**Une seule queue globale** dans Orchestrator, sans dépendance aux métiers ni aux origines. EZScore, LAB, Assistant et les autres applications sont producteurs et/ou consommateurs indépendants. Chaque job est une enveloppe opaque avec provenance et contraintes techniques. Aucun gestionnaire de queue propre à EZScore, LAB ou Assistant ne doit être recréé dans Orchestrator ; aucune file par application ni fusion des traitements métier.

Orchestrator prend en charge enqueue, priorité, ordonnancement, claim/lease/fencing, resource class, statut, attempt, retry et finalisation via contrats standard. Il ne lit ni ne juge le contenu scientifique de LAB ni la pertinence documentaire d'une expertise Assistant. L'exécution est déléguée aux workers compatibles.

## Calendrier de migration
LAB et Assistant : intégration prioritaire. EZScore : participant historique, à raccorder ultérieurement sans modifier son fonctionnement actuel. Son absence du périmètre immédiat ne le retire jamais de l'architecture cible. Ne pas déclarer une intégration EZScore opérationnelle sans preuve.

## UI
Infrastructure : états de santé techniques uniquement. Files & Jobs : **une seule table de queue globale** avec provenance, type opaque, priorité, état, worker et historique. Jusqu'au branchement effectif du registre global, la sonde LAB actuelle doit être étiquetée « observation partielle » ; ne jamais prétendre qu'elle est la queue commune ni que les jobs Assistant sont absents.

## Sécurité de migration
Ce contrat ne constitue pas une activation du gestionnaire global. Pas de claim, dispatch ni consommation de #193, #181, #182 ou #185. La parité de queue et les tests de concurrence/end-to-end restent requis.
