# v2.a16 — retrait physique de l'ancien arbre Symfony web/

Décision mainteneur : Symfony unique à la racine, aucune copie web/. Sur MAIN la prévisualisation HTTP root 8890/8891 a passé sa recette et le singleton Orchestrator/Caddy root 8790/8791 a passé start/status sous v2.a15. Le Caddy actif de ce singleton utilise déjà Caddyfile.dev-root-candidate et le docroot H:/EZS_orchestrator/public.

Ce lot supprime les fichiers **suivis par Git** dans web/, rend le docroot racine canonique dans config/caddy/Caddyfile.dev, et remplace le garde de rétention web/ par un test d'absence. Le test de parité du Caddyfile candidat est conservé, hors commentaire d'identification. Les directives de sécurité et les sites EZScore du Caddyfile DEV ne sont pas modifiés. Les anciennes règles /web/ restent dans .gitignore pour éviter tout indexage accidentel des données locales si elles subsistent.

**Attention MAIN :** des fichiers ignorés (`web/vendor`, `web/var`, `web/.env.local`, caches) peuvent rester physiquement après git pull ; Git ne les efface pas. Ne pas utiliser `git clean -fdx` ni supprimer des secrets automatiquement. Contrôler le statut du repo et inspecter les résidus avant suppression manuelle après arrêt approprié. Le singleton actif lancé avec le Caddyfile candidat n'est pas redémarré par ce commit.

Recette à exécuter sur MAIN : php tests/SymfonyLegacyWebRetirementGateTest.php, php tests/SymfonyRootCaddyCandidateContractTest.php, php tests/SymfonyRootStructureTest.php, php tests/SymfonyRootRuntimeContractTest.php ; caddy validate des fichiers dev et candidat ; requête GET 8790/ et inspection du git status.

Limites : le superviseur des backends DEV EZScore, LAB, Assistant et le lifecycle PROD normal/maintenance restent à raccorder séparément. Ne pas modifier les PID d'un processus inconnu, ni toucher à PROD. Aucun test Windows réalisé par le commit GitHub.
