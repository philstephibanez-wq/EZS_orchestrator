# Livraison 4.2c55 — restauration 4.2b et compatibilite queue / llama

**Base DEV restauree**: scripts START/STOP de la revision 4.2b `0bd850c608ad947026f671e05c7c6cd142b0b1ff`. Aucune modification de code queue, orchestrateur jobs, LAB, Assistant ou de templates.

**Adaptations indispensables**:
- START: integration du lifecycle PROD PHP/FastCGI + Caddy unifie, car l'ancien Gateway Python 4.2b a disparu. PROD conserve le mode persiste `normal` / `maintenance`; START ne le remet pas a maintenance.
- START: reintroduction du lifecycle serveur llama (Assistant, port 8720) avec controle proprietaire.
- STOP: base DEV avec nettoyage de l'Assistant IA; aucun arret PROD et aucun appel de maintenance PROD.
- Contrat de non-regression statique `tests/StartStopQueueLlama42C55ContractTest.php` : endpoints LAB queue, FastCGI 8701, facade 8702, llama 8720, START DEV/PROD, STOP DEV uniquement.
- Ancien PROD `ezs.prod.php.v1` actif est conserve sans migration forcée; v2 utilise un seul processus Caddy PROD.

**Limite**: tests et runtime Windows MAIN non executes par ce commit; verifier avant tout lancement. Aucun reboot teste.

**Recette initiale (sans operation invasive)**:
```powershell
cd H:\EZS_orchestrator
git status --short
git pull --ff-only origin master
Get-Content .\VERSION
php tests\StartStopQueueLlama42C55ContractTest.php
php tests\ProdTwoCaddy42C51ContractTest.php
php tests\RebootMode42C53ContractTest.php
php tests\ProdPhpOnly42C48ContractTest.php
php tests\ProdFastcgiDiagnostic42C50ContractTest.php
& H:\Caddy\caddy.exe validate --config .\config\caddy\Caddyfile.prod-unified --adapter caddyfile
```
Ne pas lancer START/STOP avant controles; si blocage, rapporter la premiere erreur brute. Verifier ensuite HTTP LAB queue, worker, llama health, modes PROD et deux PIDs Caddy. Les tests statiques ne remplacent pas une recette Windows.
