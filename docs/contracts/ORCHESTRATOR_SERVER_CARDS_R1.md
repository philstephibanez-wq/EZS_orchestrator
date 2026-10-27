# 1.3b15 — Présentation historique par serveur

Retour à la disposition Python du Control Center : quatre cartes DEV, PROD, LAB, Assistant au lieu de tableaux successifs. Version réelle du repo affichée. GPU fixé à gauche conservé. Chaque carte comporte état, informations succinctes, lien Ouvrir et détails repliés pour éviter le scroll.

Les commandes métier non migrées sont désactivées, notamment PROD maintenance et démarrage/arrêt des autres composants. Aucun appel PROD. Carte PROD état indéterminé tant que la maintenance authentifiée n'est pas raccordée. Sonde HTTP DEV 15 secondes inchangée (sans auto-sonde Orchestrator à travers PHP-CGI).

Tests MAIN : php web/tests/ServerCardsContractTest.php ; php web/bin/console lint:twig web/templates ; php web/bin/console lint:container ; stop/start.cmd et Ctrl+F5. Aucune modification Caddy ou des ports existants.
