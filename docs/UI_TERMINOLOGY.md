# EZS Orchestrator — terminologie UI canonique

Cette nomenclature s'applique à l'interface utilisateur et aux messages opérateur.
Les identifiants internes, clés JSON, routes et noms de modules existants ne sont pas renommés par ce contrat.

| Concept | Terme UI canonique |
|---|---|
| Application de supervision sur 127.0.0.1:8700 | Orchestrator |
| Serveur applicatif DEV / PROD / LAB | Serveur |
| Reverse proxy Caddy | Caddy |
| Passerelle applicative PROD :8510 | Passerelle |
| URL interne du serveur applicatif | URL serveur |
| Propriété d'un processus par Orchestrator | Propriété processus |
| Commit source de l'assistant | Version source |
| Commit installé sur le XPS | Version déployée |
| État de synchronisation source/XPS | État déploiement |
| Processus EZStudioLab_assistant sur le XPS | Processus assistant XPS |
| Audit de déploiement de l'assistant | Déploiement assistant → XPS |
| Audit de promotion EZScore | Déploiement DEV → PROD |

## Termes interdits dans les libellés UI

- Control Center
- Backend
- Gateway
- Transport
- Runtime XPS
- Ownership

Les noms de composants techniques Caddy, APP_ENV, CUDA, GPU, VRAM et Heartbeat sont conservés.

## États affichés

- EN LIGNE
- ARRÊTÉ
- OCCUPÉ
- PÉRIMÉ
- ERREUR
- VÉRIFICATION
- HORS LIGNE
- À JOUR
- MISE À JOUR DISPONIBLE
- NON DÉPLOYÉ
- XPS INJOIGNABLE
- NORMAL
- MAINTENANCE
- AUCUN NŒUD
