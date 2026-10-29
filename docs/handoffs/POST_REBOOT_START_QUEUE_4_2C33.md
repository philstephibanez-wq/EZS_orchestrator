# 4.2c33 — Reprise après reboot / tableau Files & Jobs

Symptômes observés le 29/10 : après reboot Windows, START refuse `EZS_START_REFUSED_SHARED_CADDY_NOT_VERIFIED` à cause de `runtime/v2-dev/processes.json` conservant des PID périmés. **Comportement initial fail-closed correct**. Correctif : effacer cet état seulement si les anciens PID Caddy/PHP sont absents et si TOUS les ports de façade partagée (8790, 8502, 8852, 8702, 8712) et backend 8791 sont libres. Sinon refus identique ; aucun processus tué ni adopté. Le lancement normal n'est pas changé.

Deuxième symptôme : test v4.2c32 `LEGACY_QUEUE_IN_UI` : le template incluait encore le panneau de sonde LAB, malgré le débranchement contrôleur. Le bloc est supprimé ; la page conserve le tableau SQLite global et les archives historiques.

Contrôle Windows : `php tests/PostRebootStartQueue42C33ContractTest.php` ; analyser AST `scripts/start.ps1`, lint Twig. Avant START réel, vérifier l'absence de processus sur les ports protégés, puis lancer START normalement. Si un port est occupé, l'Orchestrator refuse ; ne pas forcer l'arrêt ou supprimer manuellement `processes.json`. Les jobs LAB existants et la base SQLite ne sont pas modifiés. Tests runtime Windows non effectués dans le commit.
