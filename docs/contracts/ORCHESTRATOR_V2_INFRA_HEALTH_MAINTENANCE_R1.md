# V1.3b14 — Supervision Infrastructure DEV / réserve maintenance PROD

- Supervision HTTP en lecture seule de quatre endpoints 127.0.0.1 : Orchestrator 8790, EZScore DEV 8502, LAB DEV 8702, Assistant DEV 8712 ; sans test sur 8501 ou backend PROD.
- TCP et HTTP distincts, HTTP non équivalent à bonne santé métier, latence de timeout bornée ; rafraîchissement navigateur 15 secondes quand page visible.
- Point REST limité au DEV loopback ; aucune action de contrôle des processus.
- PROD : panneau maintenance affiche « État indéterminé ». Aucun toggle avant identification du mécanisme de maintenance réel, authentification, audit et preuve d'isolation Caddy PROD.
- Validation MAIN à effectuer : `php web/tests/DevHttpStatusTest.php`; `php web/bin/console lint:twig web/templates`; `php web/bin/console lint:container`; `php web/bin/console debug:router`; GET /api/v2/infrastructure/dev-health ; affichage navigateur.
- Aucun changement des ports PROD 8501, DEV 8502 ou des scripts start/stop.
