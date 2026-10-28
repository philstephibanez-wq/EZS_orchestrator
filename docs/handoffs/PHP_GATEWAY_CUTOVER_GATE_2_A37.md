# v2.a37 — décision de bascule PROD, lecture seule

## Portée
La comparaison simulée v2.a36b est validée (10/10) sur MAIN. Cela ne prouve pas que le serveur PHP intégré est acceptable en production, ni la parité SSO/médias/streaming.

`php bin/gateway_cutover_preflight.php` lit les fichiers et interroge seulement le statut local de la passerelle PROD Python sur 8510. **Aucune bascule n'est autorisée par cette version** : `can_cutover=false` est intentionnel. Le script retourne un code non nul si les prérequis fondamentaux de lecture ne sont pas satisfaits.

## Gates requis avant toute bascule
1. Gestionnaire permanent du processus PHP gateway, démarrage et redémarrage sans console.
2. Contrôles d'identité solides (chemin complet, ligne de commande, PID + date de création) avant toute action destructive.
3. Cycle PROD `start/stop` et `status` compatibles avec PHP, sans attente hardcodée de `python.exe`.
4. Tests sur instance candidate isolée avec SSO Google, cookies de session, `/internal/media/auth`, fichiers médias, réponses volumineuses et requêtes en parallèle ; valider statuts, headers et corps.
5. Plan de rollback exécutable et éprouvé : mise en maintenance contrôlée, arrêt *exclusivement* du processus identifié, restauration du lanceur Python 8510 avec vérification statut + parcours SSO/médias, puis sortie de maintenance si backend sain. **Aucune commande de rollback destructive n'est fournie sans contrôle d'identité.**

## Réception de cette version
```powershell
cd H:\EZS_orchestrator
php -l bin\gateway_cutover_preflight.php
php tests\GatewayCutoverPreflightContractTest.php
php bin\gateway_cutover_preflight.php
php bin\infrastructure.php status
```
Ne pas éteindre Python PROD, ne pas changer Caddy, ne pas toucher au fichier `H:/EZScore/var/runtime/online-gateway.json`.
