# Handoff actif — MAIN exclusivement

Toutes les applications et les moteurs d'IA utilisent MAIN. Aucun hôte secondaire et aucune route de déploiement distante ne sont autorisés. Les anciens mécanismes référencés dans les archives doivent être neutralisés et ne doivent jamais être lancés.

Caddy DEV : unique sur MAIN, partagé, conservé pendant les arrêts de backends et piloté par un gestionnaire autonome. Caddy PROD : indépendant. EZScore/LAB/Assistant/Orchestrator pilotent chacun leur backend. Les endpoints restent enregistrés dans Caddy même si un backend est arrêté.

Migration code non achevée : lanceurs historiques Python, Caddyfile DEV/PROD mélangé et gestionnaire du préflight encore à remplacer. Avant toute bascule, tests SSO, Cloudflare, médias et isolement PROD obligatoires.

## État constaté au 28/10/2026 — START/STOP v2.4b STABLE

Le mainteneur a validé sur MAIN le START/STOP global. L'Orchestrator arrête les backends PHP DEV attestés (EZScore DEV, LAB, Assistant et Orchestrator) et laisse actif **le même Caddy DEV commun**, avec ses routes déclarées même quand une application est arrêtée. PROD conserve son Caddy indépendant ; `stop.ps1` active la maintenance PROD sans arrêter le service PROD. La version figée est `2.4b` (commit `a8fb0c5cad17a61587b1596d676a6b8be7af1727`).

Ce constat remplace l'ancien état « pas encore opérationnel » pour le **seul cycle START/STOP**. Les autres travaux de migration indiqués plus haut restent à instruire sous l'issue #18 ; aucun déploiement distant ni cycle IA/worker n'est validé par cette clôture. Voir le contrat `docs/contracts/EZS_CADDY_DEV_PROD_ISOLATION_2026_10_27.md` et le handoff stable.
