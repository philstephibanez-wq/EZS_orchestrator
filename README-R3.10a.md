# EZS_orchestrator R3.10a — validation hotfix

Ce hotfix corrige uniquement des défauts de tests révélés par le bootstrap R3.10. Aucun code runtime PROD/DEV n'est modifié.

## 1. R3.6 singleton service

Le test R3.6 utilisait le même mutex Windows global que le service permanent réel :

`Global\EZS_orchestrator_service_v1`

Quand le service était réellement actif, le test échouait correctement avec `ServiceSingletonBusy`, mais cela rendait la suite impossible à exécuter sur une machine en exploitation.

Correction : les tests utilisent désormais un mutex global unique par test. Le contrat de singleton reste testé, sans contention avec le service réel.

## 2. R3.8 Caddy

Les assertions R3.8 attendaient l'ancien site-address :

`http://127.0.0.1:8501 {`

R3.10 a volontairement corrigé cette forme en :

```caddy
:8501 {
    bind 127.0.0.1
```

afin que `Host: ezscore.logandplay.com` soit accepté tout en gardant Caddy lié exclusivement au loopback.

Les tests R3.8 sont alignés sur ce contrat pour DEV `:8502` et PROD `:8501`.

## 3. R3.9 Control Center

Le test historique interdisait toute mutation PROD. R3.10 autorise maintenant uniquement le lifecycle protégé (`prod-start`, `prod-stop`, `prod-restart`, `prod-maintenance-on/off`). Le test exige désormais ces actions et continue d'interdire déploiement, DB, analyse métier, stockage et démarrage d'un service PROD depuis l'UI.

## Application locale

```powershell
cd H:\EZS_orchestrator

tar -xf "$env:USERPROFILE\Downloads\EZS_orchestrator_R3_10a_VALIDATION_HOTFIX.zip" `
    -C H:\EZS_orchestrator

powershell -ExecutionPolicy Bypass `
    -File .\bootstrap-r3_10.ps1
```

Attendu : suite complète verte puis :

`EZS_ORCHESTRATOR_R3_10_PROD_LIFECYCLE_OK`
