# Infrastructure 4.2d23 — Etat en un coup d'oeil

## Portee
Badge par application DEV/LAB/Assistant : **Operationnel (vert)** uniquement quand `application_healthy === true` est atteste et que HTTP est 2xx/3xx ; **En erreur (rouge)** si `application_healthy === false`, HTTP >=500 ou transport absent ; **A verifier (orange)** sinon. Les valeurs HTTP/TCP restent visibles dans les encarts techniques. Une redirection 302 seule ne vaut pas preuve de bonne sante. Une reponse 200 generique seule ne vaut pas non plus preuve de fonctionnement du parcours metier.

Le champ facultatif `application_healthy` n'est PAS encore produit par l'API actuelle. En consequence, les badges disponibles sans verificateur applicatif dedie restent **A verifier**, y compris pour les services joignables. Ce lot **n'invente pas une sonde**, et ne doit jamais presenter ses badges comme une validation bout-en-bout.

## Non-regression et securite
- Aucun changement des API, services Windows, reservations GPU, Messenger ou queue.
- Aucune modification des permissions de start/stop/restart, du CSRF ou de PROD.
- Pas de promotion au vert a partir du seul statut HTTP 302.
- L'etat rouge sur absence de transport est une observation technique, pas un diagnostic de panne du moteur scientifique.

## Validation
PHPUnit du contrat de code, suite complete, lint Symfony, git diff --check, controle d'encodage puis recette navigateur de plusieurs cycles. Un test de parcours applicatif canonique et sa sortie `application_healthy` restent un lot separe ; sans lui, le vert ne doit pas etre force.
