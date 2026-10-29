# Handoff 4.2c20 — Correction queue globale

Correction explicite du mainteneur : une unique queue Orchestrator, métier agnostique, toutes provenances. LAB et Assistant indépendants mais pas chacun avec leur queue Orchestrator. Révision de l'UI 4.2c19 : suppression des indicateurs de queue dans Infrastructure, étiquetage de la table LAB actuelle comme observation partielle, ajout de la provenance LAB (sonde), sans inventer les autres jobs. Contrat canonique introduit. Aucun changement de moteur, queue, START/STOP ou endpoint.

Limite : la queue réelle globale n'est pas encore rendue ; le statut Assistant n'est pas inféré d'une sonde LAB. Tests Windows/Twig à effectuer.
