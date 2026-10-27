# Handoff canonique Caddy — deux instances indépendantes

Décision du 27 octobre 2026 : **Caddy DEV** commun à toutes les applications DEV ; **Caddy PROD** dédié exclusivement à EZScore PROD. L'Orchestrator est l'unique superviseur des deux rôles. Singleton par rôle, pas singleton global.

## Invariants non négociables
- **EZScore PROD conserve exactement le port public 8501**, hôte ezscore.logandplay.com, callback Google SSO, paramètres Cloudflare, forward_auth vers 8510 et routes médias.
- **EZScore DEV conserve exactement le port public 8502**, forward_auth vers 8602 et routes médias.
- Le port 8520 de diagnostic médias du Caddyfile historique doit faire l'objet d'un arbitrage d'appartenance et de sécurité **avant** séparation. Ne pas le déplacer par supposition.
- Instances DEV et PROD : configurations, ports admin, PID, stockage runtime, logs, opérations start/stop/reload et privilèges cloisonnés ; aucune opération DEV ne peut cibler PROD.
- DEV ne peut jamais déclencher un restart/reload PROD. La disponibilité PROD reste prioritaire. Une machine physique partagée laisse subsister des risques communs de ressources/OS ; isolation stricte à prouver.
- Caddy PROD et sa configuration ne sont jamais modifiés pour accommoder DEV. Ne pas changer les DNS/SSO/Cloudflare. Pas de php -S, de tâches planifiées ou de lanceurs concurrents.

## État GitHub vérifié
- Le Caddyfile EZScore combine encore les routes 8501, 8502, 8520 et l'administration 2019. Ce fichier ne peut **pas** être utilisé tel quel par deux instances simultanées.
- L'Orchestrator Python possède encore un CaddyManager par target ; l'Assistant possède un Caddyfile distinct sur 8712 -> 8713. Nettoyage de ces mécanismes **après** équivalence REST et migration validée uniquement.
- Symfony V2 ne contrôle pas encore le cycle de vie Caddy. Aucun changement de runtime, aucune activation et aucun service démarré par ce handoff.

## Gates de livraison
1. Relecture AGENTS et dépôts, inventaire réel des processus/ports et des fichiers en usage sur MAIN.
2. Préparer deux configurations hors production, sans collision, et les faire valider par le binaire Caddy existant.
3. Valider la protection explicite contre les actions DEV touchant PROD et les chemins rollback.
4. Tester les URL existantes, Google SSO, Cloudflare et forward_auth sans interruption PROD ; procéder à une bascule contrôlée indépendante.
5. Supprimer dans le même lot validé les anciens Caddyfile, interfaces et lanceurs devenus obsolètes. Zéro Python final dans Orchestrator, sans suppression prématurée des jobs/mutex actifs.
