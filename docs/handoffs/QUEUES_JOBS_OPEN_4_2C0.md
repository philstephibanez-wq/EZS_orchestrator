# Handoff d'ouverture — 4.2c0 Queues & Jobs

**Date :** 28 octobre 2026. **Décision :** correction de la branche 4.2, migration à fonctionnalités constantes. **Base stable conservée :** 4.2b. **Issue active :** #20. **Issue #19 :** archivée, non réactivée.

Relecture GitHub : Orchestrator #1, #8, #11, #12, #15, #18 et AGENTS.md ; LAB queue R3B6/DistributedAnalysisLeaseService et LAB #16 ; EZScore AnalysisJobManager ; Assistant demeure propriétaire de l'IA. Les anciens ports XPS/Docker des issues sont historiques, pas des instructions d'exécution.

**État prouvé :** V1 avait une UI queue DEV/PROD, attempts visibles pendant running, résultats DEV et verrou GPU ; exactitude du cas PROD en live non acquise. La branche Orchestrator actuelle possède `ExclusiveLease`, mais aucune implémentation complète active de queue Messenger n'a été établie. Il faut rechercher les sources historiques et identifier leurs contrats exacts.

**Interdits :** consommation des jobs LAB #181/#182/#185, ajout de worker LAB supplémentaire, mutation PROD, changement des scripts START/STOP validés en 4.2b, modification des scientifiques ou de l'Assistant, diffusion de logs d'exécution, activation d'une file avant tests.

**Étape suivante :** audit de l'historique V1 et matrice de parité, puis implémentation itérative testée. **Aucun job exécuté et aucun test MAIN effectué lors de cette ouverture documentaire.**
