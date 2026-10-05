# EZS Orchestrator V1.0

Ce livrable clôture le périmètre V1.0 du Control Center.

## UI

Navigation par sidebar collapsable :

1. **Infrastructure**
   - service permanent ;
   - état GPU/analyse ;
   - lifecycle DEV ;
   - lifecycle PROD ;
   - maintenance PROD ;
   - ouverture DEV/PROD ;
   - logs existants, clear logique et export ZIP.

2. **Queues & Jobs**
   - queue DEV ;
   - queue PROD ;
   - contenu de queue issu du transport existant ;
   - Jobs récents avec Job / Cible / Chanson / Type / État / Date / RC analyse / Finalisation / Erreur ;
   - rafraîchissement local.

3. **Déploiement**
   - DEV fixe : `H:\EZScore_dev` ;
   - PROD fixe : `H:\EZScore` ;
   - SHA, branches, clean/dirty, pushed, fast-forward ;
   - diff fichier par fichier ;
   - protections et zones sensibles ;
   - migrations Doctrine détectées ;
   - PHP/Composer ;
   - décision GO/STOP ;
   - historique et logs détaillés ;
   - confirmation liée au SHA exact.

## Contrat de séparation

`EZScore` ne contient aucun orchestrateur de déploiement.

Le pilotage appartient exclusivement à `EZS_orchestrator`.

Le moteur V1.0 :
- ne pousse jamais vers Git ;
- ne copie jamais DEV vers PROD ;
- refuse DEV/PROD dirty ;
- exige DEV == `origin/master` ;
- exige un fast-forward ;
- bloque pendant une analyse ;
- stoppe temporairement le service permanent s'il tournait puis refait le préflight ;
- met PROD en maintenance ;
- sauvegarde la BDD SQLite PROD avec l'API backup SQLite ;
- applique `git merge --ff-only <SHA confirmé>` ;
- exécute Composer ;
- applique les migrations Doctrine à la BDD PROD existante ;
- clear le cache ;
- redémarre et vérifie PROD ;
- restaure le service permanent s'il tournait ;
- garde PROD en maintenance après échec.

Les chemins `.env.local`, `data/`, `var/storage/`, `var/runtime/`, logs/cache/venv sont protégés.

## Installation

Précondition :

```powershell
cd H:\EZS_orchestrator
git status --short
```

La sortie doit être vide.

Installation :

```powershell
tar -xf "$env:USERPROFILE\Downloads\EZS_orchestrator_V1_0.zip" `
  -C H:\EZS_orchestrator
```

## Validation obligatoire

```powershell
cd H:\EZS_orchestrator

H:\Python\pythoncore-3.14-64\python.exe -m py_compile `
  .\control_center\web.py `
  .\deployment\manager.py

H:\Python\pythoncore-3.14-64\python.exe `
  .\tests\test_orchestrator_v1_0_contract.py

git diff --check
git status --short
```

Attendu :

```text
EZS_ORCHESTRATOR_V1_0_CONTRACT_OK
```

## Démarrage

```powershell
H:\Python\pythoncore-3.14-64\python.exe -m control_center.web
```

Le navigateur doit présenter :
- Infrastructure
- Queues & Jobs
- Déploiement

## Validation avant premier déploiement réel

Ne pas cliquer sur `Déployer DEV → PROD` tant que :
- Infrastructure n'a pas été testée sans régression ;
- les queues et Jobs récents sont corrects ;
- le préflight est intégralement vert ;
- le diff DEV → PROD a été relu ;
- PHP PROD vaut `H:\PHP\php-8.5-x64\php.exe` ;
- Composer est résolu ;
- PROD est online et aucune analyse n'est active.

## V1.0.2 consolidated

Ce package inclut aussi `deployment/__init__.py` et le test d'import package, afin d'éviter l'ImportError `DeploymentPreflight` rencontré avec V1.0.
