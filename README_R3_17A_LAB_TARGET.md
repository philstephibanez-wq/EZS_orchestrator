# EZS_orchestrator R3.17A — target LAB native

Issue de référence : `#12 — R3.17 — Ajouter EZStudio_lab comme target LAB native sans régression DEV/PROD`.

## Objectif

Ajouter `LAB` comme troisième target d'analyse du **même worker permanent** :

```text
DEV -> PROD -> LAB
```

Le singleton GPU reste unique :

```text
Global\EZS_orchestrator_analysis_executor_v1
```

Aucun worker LAB supplémentaire n'est créé.

## Non-régression

R3.17A ne modifie pas :
- les roots DEV/PROD ;
- leurs ports ;
- leurs Python ;
- leurs URLs transport ;
- le lifecycle PROD ;
- Caddy ;
- le mécanisme de déploiement ;
- le mutex GPU ;
- le protocole `ezscore.analysis-job.v2`.

Le lifecycle serveur générique reste volontairement limité à `dev|prod`.
LAB est ajouté aux commandes d'analyse `queue` et `run-once`, pas aux commandes
de lifecycle serveur.

## LAB

```text
root             H:\EZStudio_lab
backend/public   8701
transport        http://127.0.0.1:8701
analysis Python  H:\Python\pythoncore-3.14-64\python.exe
entrypoint       H:\EZStudio_lab\analysis\worker_entrypoint.py
```

Token :
- override orchestrator : `EZS_LAB_ANALYSIS_TOKEN`
- sinon `.env.local` de EZStudio_lab : `EZSTUDIO_ANALYSIS_WORKER_TOKEN`

## Planner

DEV et PROD gardent strictement leur règle actuelle :
leur Python doit appartenir à leur checkout.

LAB constitue le seul cas où le Python peut être externe au checkout. Il doit
correspondre exactement à l'exécutable configuré pour LAB et ne doit pas être
sous les roots DEV/PROD.

Les chemins d'un job restent isolés :
- DEV interdit PROD et LAB ;
- PROD interdit DEV et LAB ;
- LAB interdit DEV et PROD.

## Installation

Créer une branche locale avant application :

```powershell
cd H:\EZS_orchestrator
git switch -c feature/r3-17a-lab-target
```

Dézipper :

```powershell
tar -xf "$env:USERPROFILE\Downloads\EZS_orchestrator_LAB_R3_17A.zip" `
  -C H:\EZS_orchestrator `
  --strip-components=1
```

Appliquer :

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\apply-lab-r3_17a.ps1
```

Puis lancer la suite complète :

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\preflight-lab-r3_17a.ps1
```

## Redémarrage du service permanent

Uniquement après tests verts :

```powershell
python -m service.service_cli stop
python -m service.service_cli start --target all --poll-seconds 2
python -m service.service_cli status
```

## Contrôle

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\status-lab-r3_17a.ps1
```

Avant le raccordement d'EZStudio_lab, la commande LAB peut indiquer une erreur
de transport/token. DEV et PROD doivent rester fonctionnels.

Après raccordement d'EZStudio_lab, `queue --target lab` doit répondre et les
tentatives LAB seront écrites sous :

```text
H:\EZS_orchestrator\runtime\jobs\lab
```

Le Control Center les affichera automatiquement via `JobHistory`.
