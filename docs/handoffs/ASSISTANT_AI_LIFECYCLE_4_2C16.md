# 4.2c16 — IA indépendante au sein de START/STOP

Les scripts canoniques `scripts/start.ps1` et `scripts/stop.ps1` contiennent le cycle IA : processus `llama-server.exe` unique sur 127.0.0.1:8720, modèle existant Qwen2.5-1.5B, contexte 4096, une place, CPU prudent. Démarrage Windows `Start-Process -WindowStyle Hidden`. Aucun Python, Web, guardian ou job déclenché par cette tranche.

Un listener 8720 **sans état attesté** reste intact au START/STOP. Le STOP exige fichier d'état, PID, création du processus, chemin exécutable, arguments modèle/port et propriété du listener. Si état incohérent, refus fail-closed. L'état est placé sous `runtime/v2-dev/assistant-ai.json`, verrou `assistant-ai.lock`. Pas de tâche planifiée ni conteneur.

**Limites :** recette réelle START/STOP encore à effectuer, PowerShell sur Windows. L'arrêt manuel du superviseur 4.2c15 est nécessaire *si l'opérateur souhaite que START prenne la propriété du moteur* ; ne pas tuer ce service depuis START. Les appels existants START/STOP ne doivent pas perdre leurs protections historiques. L'échec d'une phase antérieure peut empêcher d'atteindre la phase IA ; aucune compensation globale n'est introduite. Cette tranche ne consomme aucun job LAB. La qualification GPU et la contre-expertise musicale restent indépendantes.

Tests : contrat PHP `tests/AssistantAiLifecycle42C16ContractTest.php`, syntaxe PowerShell AST, tests START/STOP et identité port sous Windows avant validation en production.
