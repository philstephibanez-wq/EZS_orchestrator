# Contrat canonique : MAIN uniquement

La seule machine autorisée pour EZScore, LAB, Assistant et Orchestrator est MAIN. Toute voie d'exécution vers un nœud distant, tout démarrage distant, SSH ou mécanisme de déploiement externe est interdit dans l'architecture cible. Les références historiques ne sont pas des autorisations d'exécution.

Sur MAIN, un Caddy DEV commun conserve les routes des applications même lorsque leurs backends sont arrêtés ; un Caddy PROD indépendant est réservé à EZScore PROD. Les lanceurs applicatifs gèrent uniquement leurs backends. Si Caddy DEV est arrêté, ils utilisent le même gestionnaire Caddy DEV autonome, sans dépendre du serveur Web Orchestrator. Aucun lanceur ne doit créer un deuxième Caddy DEV ni arrêter le Caddy partagé lorsqu'il arrête un backend.

Port PROD 8501, port DEV 8502, façade LAB 8702, backend LAB 8701 ; préserver SSO Google, Cloudflare, forward_auth et médias. Le port médias diagnostic 8520 exige une attribution validée avant séparation des configurations. PID, verrous, admin API et logs DEV/PROD doivent être indépendants. Une route dont le backend est arrêté doit retourner une indisponibilité, sans suppression dynamique de l'URL.

Écarts constatés dans GitHub : EZScore et LAB utilisent encore les gestionnaires Python de l'Orchestrator ; l'Assistant possède un ancien lanceur Caddy distinct ; l'ancien Caddyfile EZScore mélange DEV et PROD ; le préflight Symfony V2 refuse encore tout Caddy déjà lancé. Aucun de ces écarts n'est réputé migré.

Gates : inventorier et neutraliser les anciennes voies d'exécution ; créer le singleton Caddy DEV ; scinder les Caddyfile sans interrompre PROD ; migrer les lanceurs canoniques ; tester authentification, médias, indisponibilité des backends et contrôle de propriété ; seulement ensuite purger les chemins legacy. Ce document ne lance et n'arrête aucun service.

## État validé — 28 octobre 2026 : cycle de vie v2.4b stable

**Contrat appliqué sur MAIN pour START/STOP** : les backends FastCGI DEV sont arrêtés/démarrés dans leur périmètre (EZScore DEV 8602/8862, LAB 8701, Assistant 8713, Orchestrator 8791). Le Caddy DEV commun conserve les façades 8502, 8852, 8702, 8712 et 8790 lorsque les backends sont arrêtés. Les PID backend sont attestés avant arrêt. La maintenance d'EZScore PROD est activée par le STOP global, sans arrêt du Caddy PROD ni déploiement PROD. L'opérateur a confirmé le succès de START/STOP sur MAIN ; version de référence `2.4b`, stable pour **ce cycle de vie**.

**Portée de la validation** : cette stabilisation ne signifie pas que les lanceurs historiques de chaque dépôt ont tous été migrés ni que les exigences transversales du présent contrat (SSO, Cloudflare, médias, suppression de toutes voies legacy, queues, workers/Qwen/guardian et supervision autonome) ont été entièrement recettées. Le mécanisme actuellement opérationnel est documenté, ses écarts résiduels restent suivis dans l'issue #18. Ne pas réintroduire de Caddy par application ; ne pas conclure de cette stabilité que les workers IA sont gérés par START/STOP.

Traçabilité : correctif cycle global `9cf15c1e313e8130291f9fc4f273c2b379dade9d`; promotion stable `a8fb0c5cad17a61587b1596d676a6b8be7af1727`; handoff `docs/handoffs/LIFECYCLE_STABLE_2_4B_2026_10_28.md`.
