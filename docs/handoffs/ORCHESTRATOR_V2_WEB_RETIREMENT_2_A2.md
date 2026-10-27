# Handoff v2.a2 — verrouillage du retrait de web/

## Contexte
La préparation locale précédente de suppression de `web/` a exposé un grand volume de fichiers générés non suivis, car `web/.gitignore` devait disparaître. L'état MAIN rapporté avant ce lot est propre sur `af3fdb0` / `2.a1`, et `git check-ignore -v` résout encore les exclusions via `web/.gitignore`. Les quatre Caddyfiles DEV pointent toujours vers `web/public`.

## Modifications v2.a2
Les cinq exclusions historiques sont reportées au `.gitignore` racine, sans retirer leur copie `web/.gitignore`. Un test contractuel durable empêche une suppression du dossier ou une activation Caddy/START anticipées. Le contrat de retrait explicite les preuves obligatoires.

## Tests
Revue statique GitHub effectuée. Les tests PHP et les commandes `git check-ignore`, `git status` et `git diff --check` restent **à exécuter sur MAIN après pull**. Aucun test HTTP réel, lifecycle, API jobs, Windows sans flash console ou non-régression d'orchestration n'est revendiqué.

## Périmètre non modifié
Aucun fichier de `web/` supprimé, aucun fichier Caddy modifié, aucun lanceur modifié, aucun service démarré, aucun job consommé, aucun changement LAB/Assistant/PROD. Aucun nettoyage local distant possible via GitHub seul.

## Suite bloquée
Implémenter la parité Symfony des API/actions/queues/lifecycle et valider Caddy root en HTTP réel dans une recette isolée et réversible. Après cela uniquement : transfert des tests historiques, bascule, retrait de `web/` et remplacement du test de transition par un test de non-régression final. Maintenir l'issue #18 ouverte.

## Correction v2.a3 — fins de ligne Windows
La première recette MAIN de v2.a2 a échoué avec `LEGACY_IGNORE_PROTECTION_MISSING:/web/vendor/` alors que `.gitignore` contient la règle et que `git status` est propre. Le contrôle `preg_match(...$/m)` ne gérait pas les fins de ligne CRLF Windows : le caractère `\r` précède la fin de ligne et empêche l'égalité. v2.a3 remplace les correspondances de regex par une lecture ligne à ligne (`CRLF`, `LF`, `CR`) et une comparaison stricte. Aucun changement de règles Git, de services ou de chemin runtime. Validation statique et contre-exemple PHP local effectués ; recette Windows intégrale à refaire.

## v2.a4 — identité HTTP preview Symfony
La sonde HTTP isolée exige désormais, outre la page Twig, les signatures JSON spécifiques de `/api/status` et la barrière jobs `/api/jobs` HTTP 503. Cela empêche de qualifier par erreur une vieille interface comme Symfony V2. Aucune activation de service et aucune suppression de `web/`. Test réseau MAIN non exécuté à la publication.
