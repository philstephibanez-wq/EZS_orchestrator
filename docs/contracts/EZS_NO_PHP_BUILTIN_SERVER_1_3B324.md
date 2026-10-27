# Contrat transversal — aucun `php -S` dans la plateforme EZS (v1.3b324)

Décision explicite du mainteneur du 27 octobre 2026 : le serveur HTTP intégré de PHP (`php -S`, équivalents et variantes de commande) est **interdit dans toute la plateforme EZS**, en DEV comme en PROD, y compris LAB, Assistant, scripts de secours, démarrages manuels et automatismes. Tous les sites Web utilisent Caddy. L'Orchestrator est seul responsable de leurs démarrages/arrêts/redémarrages et des configurations Caddy.

La présence historique de `php -S` dans des fichiers source, des archives et des tests de migration n'autorise pas son exécution. Aucun fallback silencieux vers `php -S` n'est permis.

## Écart GitHub confirmé

- `EZS_orchestrator/server_manager/manager.py` : `ServerManager.start()` invoque encore PHP avec `"-S"` et `"-t"`. `ServerManager.view/adopt/stop` reconnaissent toujours cette identité. Ce chemin est incompatible avec le contrat cible.
- La chaîne PROD existante : Cloudflare → Caddy PROD 8501 → Gateway HTTP 8510 → PHP HTTP 8511. **Ne pas remplacer seulement l'exécutable** : la Gateway attend HTTP, FastCGI est un protocole différent.
- `EZScore/scripts/start.ps1` appelle encore `ServerManager` et `CaddyManager` historiques. Ce lanceur n'est plus autorité dans l'architecture cible.
- EZScore DEV 8602 dispose déjà d'un singleton `php-cgi.exe` opérationnel, piloté par `EZS_orchestrator/scripts/app-control.ps1`; sa façade Caddy 8502 reste à raccorder.

## Conditions de migration bloquantes

1. Inventorier les chemins d'exécution des dépôts EZS, y compris scripts de secours, tâches planifiées et runtime ; distinguer les occurrences historiques des lancements exécutables.
2. Remplacer les chemins de lancement de backends PHP HTTP par PHP-CGI/FastCGI ou une intégration compatible avec Caddy. Aucun `php -S` direct ou via fallback.
3. Configurer les routes Caddy exclusivement depuis EZS_orchestrator. Instances Caddy DEV/PROD séparées ; interdiction de démarrer des Caddy par application.
4. Adapter toute Gateway HTTP qui attend actuellement `php -S`, sans altérer les sources de `H:\EZScore` PROD. Maintenir Cloudflare, SSO, cookies, forward_auth et contrôle des médias.
5. Ajouter des tests automatisés refusant les nouveaux chemins `php -S`, puis supprimer la liste des exceptions historiques avant de déclarer le contrat satisfait.
6. Conserver PROD en maintenance jusqu'à demande explicite de sortie ; ne pas interrompre sa chaîne fonctionnelle avant préflight, recette HTTP authentifiée et rollback éprouvé.

**État de cette révision : contrat enregistré ; migration d'exécution NON réalisée et non revendiquée.**
