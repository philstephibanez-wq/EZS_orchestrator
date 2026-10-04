# EZS_orchestrator R3.10 — exploitation PROD protégée

## Objectif

R3.10 remplace la politique R3.9 « PROD lecture seule » par une **exploitation protégée**.

Actions PROD autorisées depuis le Control Center :

- démarrer toute la chaîne PROD ;
- redémarrer toute la chaîne PROD ;
- arrêter toute la chaîne PROD ;
- passer en mode maintenance ;
- revenir en mode normal ;
- lire les états backend / gateway / Caddy.

Les actions métier, DB, storage, analyse et déploiement restent hors de ce périmètre.

## Topologie contractuelle

```text
Cloudflare
  -> Caddy PROD 127.0.0.1:8501
  -> Gateway PROD 127.0.0.1:8510
  -> Symfony PROD 127.0.0.1:8511
```

Racine PROD : `H:\EZScore`.

Le correctif incident Caddy est rendu permanent :

```caddy
:8501 {
    bind 127.0.0.1
```

Ainsi le Host public `ezscore.logandplay.com` est accepté tout en gardant le listener exclusivement loopback.

## Installation

```powershell
cd H:\EZS_orchestrator

tar -xf "$env:USERPROFILE\Downloads\EZS_orchestrator_R3_10_PROD_LIFECYCLE.zip" `
    -C H:\EZS_orchestrator

powershell -ExecutionPolicy Bypass -File .\bootstrap-r3_10.ps1
```

Le ZIP contient uniquement les fichiers nouveaux/modifiés R3.10.

## Relancer le Control Center

Fermer l'ancien processus R3.9 (Ctrl+C dans sa console), puis :

```powershell
cd H:\EZS_orchestrator
powershell -ExecutionPolicy Bypass -File .\scripts\start_control_center.ps1
```

URL : `http://127.0.0.1:8700/`.

## CLI R3.10

```powershell
$Python = "H:\Python\pythoncore-3.14-64\python.exe"
cd H:\EZS_orchestrator

& $Python -m control_center.cli status
& $Python -m control_center.cli prod-start
& $Python -m control_center.cli prod-maintenance-on
& $Python -m control_center.cli prod-maintenance-off
& $Python -m control_center.cli prod-restart
& $Python -m control_center.cli prod-stop
```

Les anciennes commandes `server-start prod`, `server-stop prod`, `server-restart prod` sont volontairement refusées afin qu'une opération PROD ne puisse plus ne gérer que `8511` et oublier `8510/8501`.

## Validation live recommandée

Après installation :

```powershell
$Python = "H:\Python\pythoncore-3.14-64\python.exe"
cd H:\EZS_orchestrator

& $Python -m control_center.cli status
```

Puis tester depuis le Control Center :

1. Maintenance ON : `https://ezscore.logandplay.com/` doit afficher la maintenance.
2. Mode normal : le catalogue/login normal revient sans restart Cloudflare.
3. Redémarrer PROD : les trois couches `8511`, `8510`, `8501` doivent revenir ONLINE.
4. Requête Host publique locale :

```powershell
$r = Invoke-WebRequest `
    -Uri "http://127.0.0.1:8501/" `
    -Headers @{ Host = "ezscore.logandplay.com"; "X-Forwarded-Proto" = "https" } `
    -UseBasicParsing `
    -MaximumRedirection 10 `
    -TimeoutSec 10

"STATUS=$($r.StatusCode)"
"LENGTH=$($r.RawContentLength)"
"TYPE=$($r.Headers['Content-Type'])"
```

Attendu en mode normal : HTTP 200 avec contenu HTML non vide.

## Sécurité

- PROD reste verrouillé sur `H:\EZScore` / `APP_ENV=prod`.
- Les ports PROD sont vérifiés explicitement : backend 8511, gateway 8510, public 8501.
- Stop/restart PROD sont refusés pendant une analyse active.
- Le gateway est désormais lancé par l'Orchestrator (`gateway_manager.server`) et ne dépend plus du vieux Worker desktop.
- Aucun fallback DEV -> PROD / PROD -> DEV n'est ajouté.
