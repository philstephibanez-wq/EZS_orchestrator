# 1.3b26 — propriété PHP-CGI 8791

Incident MAIN: listener 8791 PID 28280 alors que metadata php_pid=0, HTTP 200 ; arrêt antérieur annoncé à tort. L'arrêt ne réinitialise plus php_pid si 8791 écoute encore. Le status signale BACKEND_PID et OWNERSHIP_MISMATCH. Le start n'adopte jamais un PID port 8791 différent de celui démarré. Le Caddy DEV partagé ne doit jamais être arrêté par ces actions.

Dans l'état actuel MAIN, ne pas relancer un start ou tuer 28280 automatiquement : vérifier le PID et la persistance de son identité, puis effectuer une récupération explicitement approuvée et traçable, après arrêt de toute requête active. Le présent patch ne revendique pas de récupération d'un processus dont le PID n'a plus de preuve de propriété. Contrat statique fourni, test Windows requis.
