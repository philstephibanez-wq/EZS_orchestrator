# v2.a12 — reprise du singleton de recette 8790/8791

Implémentation limitée, fail-closed : les commandes scripts/start.cmd et stop.cmd appellent un même gestionnaire PowerShell `scripts/v2_lifecycle.ps1`; `scripts/status.cmd` permet le contrôle. Le lanceur utilise PHP-CGI 8791 et le Caddyfile candidat root 8790, identifie par PID, exécutable, signature CLI et port, conserve un état sous runtime/v2-dev, sérialise start/stop et refuse les ports occupés. Le stop arrête ces deux processus uniquement s'ils sont formellement possédés. PROD 8501/8510 et son Caddy ne sont jamais ciblés.

**Ce lot n'est pas le superviseur DEV complet** : EZScore DEV, LAB et Assistant n'ont pas encore de gestionnaires raccordés. Si leurs ports sont actifs, stop refuse l'arrêt global afin de ne pas présenter un arrêt incomplet comme réussi. Il ne faut pas activer ce lanceur en parallèle du Caddy DEV partagé déjà en service ; un Caddy préexistant sur 8790 fait échouer start.

Le dossier `web/` reste temporairement sous protection : le retirer avant de migrer ses tests et config PROD risquerait de détruire des preuves et des chemins actifs. La suppression est expressément demandée et doit suivre la validation de ce bootstrap, sans devenir une excuse pour les fonctions Jobs non implémentées.

Vérifications MAIN exigées avant usage : lint Parser PowerShell, tests du contrat, caddy validate, ports 8790/8791 libres, start/status/stop, deuxième start concurrent refusé, idempotence stop, vérification PID, contrôle PROD intact. Aucune exécution sur MAIN n'a été réalisée depuis GitHub.
