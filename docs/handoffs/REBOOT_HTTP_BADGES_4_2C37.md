# v4.2c37 — Incident reboot et statuts HTTP

Contrat immédiat dashboard : HTTP 2xx/3xx = vert, 4xx/5xx = rouge, sans réponse avec listener TCP = orange, absence de réponse et de listener = gris. Le port TCP ouvert ne suffit jamais à déclarer l'application disponible. Régression observée : HTTP 502 DEV/LAB/Assistant s'affichait « Erreur HTTP » en vert. Test statique dédié. Aucun backend, Caddy, ni fichier d'état modifié.

**Recette de résilience non close** : reboot réel avec états périmés et services indépendants PROD / DEV / LAB / Assistant doit encore être testé. PROD : `start.ps1 -ProdAction status` confirme `ready=False state_present=True` ; ne pas effacer cet état ou lancer START aveuglément. Les HTTP 502 proviennent des backends non prêts. Le chantier de cycle de vie complet reste ouvert, sans prétendre que l'incident réseau est réparé par le badge.
