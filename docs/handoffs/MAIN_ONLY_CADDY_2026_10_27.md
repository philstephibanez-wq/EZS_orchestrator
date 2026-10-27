# Handoff actif — MAIN exclusivement

Toutes les applications et les moteurs d'IA utilisent MAIN. Aucun hôte secondaire et aucune route de déploiement distante ne sont autorisés. Les anciens mécanismes référencés dans les archives doivent être neutralisés et ne doivent jamais être lancés.

Caddy DEV : unique sur MAIN, partagé, conservé pendant les arrêts de backends et piloté par un gestionnaire autonome. Caddy PROD : indépendant. EZScore/LAB/Assistant/Orchestrator pilotent chacun leur backend. Les endpoints restent enregistrés dans Caddy même si un backend est arrêté.

Migration code non achevée : lanceurs historiques Python, Caddyfile DEV/PROD mélangé et gestionnaire du préflight encore à remplacer. Avant toute bascule, tests SSO, Cloudflare, médias et isolement PROD obligatoires.
