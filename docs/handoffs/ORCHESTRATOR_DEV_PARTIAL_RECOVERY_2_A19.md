# v2.a19 — récupération contrôlée PHP-CGI DEV

MAIN v2.a18 : les contrats et les trois Caddyfiles passent ; `EZS_STATUS php_owned=False caddy_owned=True state_present=True`. L'ancien run tente alors un `start` interdit par la présence du state. PROD n'a pas été atteinte.

Le lifecycle DEV expose maintenant `repair` sous verrou, uniquement lorsque Caddy DEV (8790, 8502, 8852) appartient exactement au PID enregistré, que le PID PHP stocké a disparu et que 8791 est libre. Il redémarre seulement PHP-CGI 8791, vérifie son ownership puis actualise le PID dans le state. Refus si processus ou port étranger / encore actif. Jamais d'arrêt Caddy ni PROD pendant la réparation. `infrastructure_restore.ps1 -Action start` utilise cette réparation uniquement sur statut précis `php_owned=False caddy_owned=True state_present=True` ; sinon refuse sans forcer le singleton.

Validation GitHub statique seulement. Recette MAIN : `git pull --ff-only origin master` ; `powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\infrastructure_restore.ps1 -Action start` ; vérifier ensuite `-Action status`. Ne pas exécuter de commande de nettoyage de PID. Si un processus PHP subsiste, la réparation refuse et nécessite un diagnostic non destructif. PROD est démarrée en maintenance uniquement après DEV sain.
