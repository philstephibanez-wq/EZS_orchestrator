# 4.2c7 — Correctif bloquant contrôleur historique jobs

**Incident MAIN remonté le 28/10/2026 :** `php -l src/Module/Infrastructure/Controller/LegacyReadOnlyController.php` échoue : `unexpected token "private"` ligne 49 dans 4.2c6. Le test autonome du lecteur `LegacyHistoryReadOnly42C6ContractTest.php` est OK, mais n'avait pas compilé le contrôleur ; la livraison 4.2c6 n'est donc pas validée.

**Cause vérifiée sur GitHub :** la branche `if (!$this->loopback($request))` contenait la lecture de l'historique et ne se fermait pas correctement, et l'import de `LegacyJobHistoryReader` manquait.

**Correction :** réponse 403 explicite si hôte/IP non loopback, lecture locale de l'historique uniquement après ce contrôle, réponse `historical_result_json` avec `live_queue=false`, import du lecteur, syntaxe des méthodes corrigée. Nouveau test de garde réalisant une vérification PHP `-l` du contrôleur.

**Aucune mutation** de jobs, aucun claim/worker, pas de changement START/STOP, LAB, PROD ou Assistant. Recette à exécuter sur MAIN. Les anciens contrats de lecture seule demeurent.
