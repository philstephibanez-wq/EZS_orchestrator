# R1H : superviseur résident ROOT uniquement

- ROOT = PHP-CGI `127.0.0.1:8791`, santé applicative `http://127.0.0.1:8790/health`.
- Un résident unique réemploie le tick canonique avec `-RootOnly`. Dans ce mode, le tableau des cibles Caddy est vide. Le tick ne démarre, n'arrête et ne sonde aucun Caddy DEV ou PROD.
- La tâche Windows `EZS_ROOT_resident` est indépendante de `EZS_orchestrator_supervisor` et créée désactivée. Le compte interactif existant est conservé.
- L'ancienne tâche demeure désactivée ; son ancienne responsabilité PROD n'est pas restaurée automatiquement.
- La récupération FastCGI R1F conserve les contrôles d'identité, d'intention et temporisations. Un PID étranger/ambigü n'est jamais arrêté.
- Une réponse HTTP 502 signifie ROOT dégradé même si le processus existe. Un résident actif ne prouve pas HTTP 200.
- Installation des sources, puis enregistrement de tâche désactivée, puis activation et recette sont des étapes distinctes. Aucune activation automatique pendant la copie des sources.
- Retour arrière : désactiver et supprimer uniquement la nouvelle tâche, restaurer les sauvegardes des fichiers modifiés et VERSION. Ne pas réactiver implicitement la tâche historique (périmètre PROD gelé).
- Limite : le souci FastCGI/socket 8791 reste non résolu par la résidence.
