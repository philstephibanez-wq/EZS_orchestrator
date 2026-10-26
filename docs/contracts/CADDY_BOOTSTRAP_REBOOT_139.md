# v1.3a(9) — démarrage Caddy, capture d'erreurs et résilience

Après reboot et installation de v1.3a(8), MAIN a confirmé : service permanent actif, Control Center écoutant sur 8700, PROD Caddy healthy, DEV/LAB non reconnus par CaddyManager, échec splash avec seulement « Traceback (most recent call last): », caddy-start.log vide.

Cause technique suspectée et corrigée : avec Windows PowerShell 5.1 et ErrorActionPreference=Stop, une ligne stderr provenant de Python dans le pipeline 2>&1 interrompait prématurément le lanceur, empêchant la capture du traceback complet et la suite du bootstrap. Chaque cible est désormais exécutée avec stdout et stderr redirigés dans des fichiers distincts sous logs, et les erreurs de lancement sont traitées individuellement. Une erreur Caddy ne bloque plus la mise à disposition du Control Center. Instances Caddy déjà actives laissées intactes par CaddyManager.start ; aucune commande stop.

Contrôle : logs/caddy-start-{dev,prod,lab}.{out,err}.log et logs/caddy-start.log. Tests contractuels mis à jour. Exécution Windows PowerShell 5.1 et démarrage MAIN non encore validés ; ne pas annoncer le correctif comme testé de bout en bout. Supervision en continu hors du périmètre.
