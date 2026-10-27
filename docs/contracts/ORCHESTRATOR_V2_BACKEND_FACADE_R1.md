# 1.3b17 — Distinguer backend LAB et façade DEV

Supervision lecture seule des façades EZScore DEV 8502, LAB 8702 et Assistant 8712, plus backend LAB existant 8701. Aucune sonde PROD. Le backend LAB est visible dans les détails de carte ; une façade arrêtée ne doit pas masquer un backend en marche. Aucune auto-sonde 8790 pour éviter interblocage PHP-CGI monoprocessus. Pas de commande start/stop ni de bascule Caddy.

Tests MAIN: `php web/tests/DevHttpStatusTest.php`, `php web/bin/console lint:twig web/templates`, redémarrage `scripts/stop.cmd` puis `scripts/start.cmd`, affichage de la carte LAB avec détails ouverts. Aucun impact PROD.
