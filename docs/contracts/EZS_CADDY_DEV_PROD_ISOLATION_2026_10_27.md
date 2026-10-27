# Contrat canonique : MAIN uniquement

La seule machine autorisée pour EZScore, LAB, Assistant et Orchestrator est MAIN. Toute voie d'exécution vers un nœud distant, tout démarrage distant, SSH ou mécanisme de déploiement externe est interdit dans l'architecture cible. Les références historiques ne sont pas des autorisations d'exécution.

Sur MAIN, un Caddy DEV commun conserve les routes des applications même lorsque leurs backends sont arrêtés ; un Caddy PROD indépendant est réservé à EZScore PROD. Les lanceurs applicatifs gèrent uniquement leurs backends. Si Caddy DEV est arrêté, ils utilisent le même gestionnaire Caddy DEV autonome, sans dépendre du serveur Web Orchestrator. Aucun lanceur ne doit créer un deuxième Caddy DEV ni arrêter le Caddy partagé lorsqu'il arrête un backend.

Port PROD 8501, port DEV 8502, façade LAB 8702, backend LAB 8701 ; préserver SSO Google, Cloudflare, forward_auth et médias. Le port médias diagnostic 8520 exige une attribution validée avant séparation des configurations. PID, verrous, admin API et logs DEV/PROD doivent être indépendants. Une route dont le backend est arrêté doit retourner une indisponibilité, sans suppression dynamique de l'URL.

Écarts constatés dans GitHub : EZScore et LAB utilisent encore les gestionnaires Python de l'Orchestrator ; l'Assistant possède un ancien lanceur Caddy distinct ; l'ancien Caddyfile EZScore mélange DEV et PROD ; le préflight Symfony V2 refuse encore tout Caddy déjà lancé. Aucun de ces écarts n'est réputé migré.

Gates : inventorier et neutraliser les anciennes voies d'exécution ; créer le singleton Caddy DEV ; scinder les Caddyfile sans interrompre PROD ; migrer les lanceurs canoniques ; tester authentification, médias, indisponibilité des backends et contrôle de propriété ; seulement ensuite purger les chemins legacy. Ce document ne lance et n'arrête aucun service.
