# 4.2c15 — Superviseur IA isolé (candidat explicite)

Implémentation durable : commande Symfony `ezs:assistant-ai:serve`. Sans `--run`, elle vérifie seulement la présence du binaire et du GGUF. Avec `--run` (opt-in), elle acquiert un verrou non bloquant, refuse un port 8720 déjà occupé, lance uniquement `llama-server.exe`, garde un handle Symfony Process sur son enfant et vérifie `GET /health`. Le superviseur doit rester actif ; quitter le superviseur arrête uniquement son enfant. Aucun kill par PID externe.

Le contexte historique 24576 n'est pas repris sans qualification RAM/VRAM. Démarrage prudent CPU `--gpu-layers 0 --ctx-size 4096 --parallel 1`. Cette configuration est une **dérogation de sécurité provisoire**, pas une preuve de parité de performance GPU. Le service est un candidat CLI ; **aucun lancement automatique sans console par START/STOP n'est encore livré**. Sur Windows, il faut vérifier en condition réelle l'identité du processus, l'absence de fenêtre intempestive et la terminaison propre avant intégration permanente.

Version 4.2c15 : aucun fichier Assistant ni LAB changé. Job #193 et jobs #181/#182/#185 intouchés. L'ancienne interface 18720 n'est pas restaurée par ce commit. Le superviseur ne publie pas de résultat d'expertise, et le circuit LAB → Assistant → LAB reste incomplet.

Recette : `php -l src/Module/Coordination/AssistantAiSupervisorCommand.php`, `php tests/AssistantAiSupervisor42C15ContractTest.php`, `php bin/console ezs:assistant-ai:serve` (préflight seulement). N'exécuter `--run` qu'après validation de l'environnement et décision explicite de démarrer le moteur. Ce code ne prétend pas assurer une persistance après extinction du processus superviseur.
