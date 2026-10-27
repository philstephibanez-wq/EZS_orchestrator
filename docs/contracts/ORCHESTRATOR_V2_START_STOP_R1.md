# 1.3b13 — Start / Stop / Status Symfony DEV

Les commandes existantes scripts/start.cmd et scripts/stop.cmd sont redirigées vers le runtime Symfony V2, scripts/status.cmd est ajouté. Le lanceur Python historique n'est plus appelé par ces deux points d'entrée. Scripts/v2_lifecycle.ps1 est **l'unique implémentation** de cette commande à trois actions.

Start vérifie PHP-CGI, Caddy et l'autoload, l'absence de Caddy concurrent et la disponibilité 8790/8791 ; lance les deux processus sans fenêtre, vérifie le HTTP 200 de l'API et écrit les PID dans runtime/v2-dev/processes.json en UTF-8 sans BOM. Un verrou de fichier sérialise les appels start/stop/status.

Stop ne touche qu'aux PID sauvegardés correspondant **à la fois** à l'exécutable attendu et à la signature de commande attendue. Aucun kill par port. Stop ne modifie jamais EZScore PROD 8501, EZScore DEV 8502 ni LAB 8701 et n'arrête aucun autre Caddy. Le runtime de préflight 8790/8791 reste local et distinct d'une future configuration Caddy DEV partagée.

Limites : le Caddy DEV commun et la reprise après crash restent à intégrer ; ceci lance le V2 HTTP **sur le préflight**, pas une architecture PROD. Si Caddy est déjà actif, start refuse de créer un doublon. Un état partiel est un blocage conservateur. Ne pas utiliser launch.bat : ancien point d'entrée Python encore à nettoyer avec ses dépendances après validation de la parité fonctionnelle. Aucun job scientifique n'est démarré par start.

Tests MAIN : git pull ; scripts\\status.cmd ; scripts\\start.cmd ; scripts\\status.cmd ; GET http://127.0.0.1:8790/ ; scripts\\stop.cmd ; scripts\\status.cmd ; vérification ports. Ne jamais tuer le PID LAB. Tests non exécutés lors du commit.
