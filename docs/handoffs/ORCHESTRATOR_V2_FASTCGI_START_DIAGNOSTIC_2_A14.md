# v2.a14 — diagnostic du démarrage PHP-FastCGI sur MAIN

Après arrêt et singleton propre, start.cmd échoue de façon répétée sur EZS_START_FASTCGI_FAILED. La commande manuelle php-cgi.exe -b 127.0.0.1:8791 réussit : PID 33564 écoute bien sur 8791. La cause du dysfonctionnement de Start-Process n'est pas encore démontrée.

Cette livraison conserve les protections de propriété et le stop de v2.a13. Pour PHP-CGI lancé par le superviseur, elle redirige stdout/stderr dans un dossier temporaire système hors Git et, en cas d'échec, publie PID lancé, état vivant, propriétaires observés du port et chemin du stderr, ainsi que le contenu de stderr si présent. Le message d'échec est discriminant et aucune donnée de sortie ne va dans le dépôt. Aucune revendication de correction définitive avant le résultat réel sur MAIN.

Recette : arrêter normalement le php-cgi manuel depuis sa propre console, contrôler port 8791 libre et état singleton absent, lint PowerShell et test statique, puis start.cmd/status.cmd. Si échec transmettre diagnostic sans publier de secret. PROD non touchée. La suppression web/ reste non réalisée.
