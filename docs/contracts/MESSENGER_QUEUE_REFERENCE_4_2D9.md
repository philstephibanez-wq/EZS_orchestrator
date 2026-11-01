# Contrat 4.2d9 — adaptateur de référence Messenger non activé

Le message `QueueJobReference` ne porte que `jobId`, `producer`, `claimGeneration`.
Il est immuable, sans payload métier ni secret de lease. Les producteurs autorisés
pour cet adaptateur sont `lab`, `assistant`, `ezscore` ; PROD n'est pas activé.

`QueueJobReferenceAdapter::inspect()` est une lecture **strictement read-only**
via `QueueRestReadModel` et un chemin SQLite explicite. Elle vérifie le producteur
et la génération courante, retourne une projection excluant les secrets et
rejette toute référence introuvable ou périmée.

`config/services.yaml` exclut explicitement le DTO de l'autowiring Symfony.
Ce lot **n'enregistre aucun handler Messenger**, aucune route, aucun transport,
aucun consumer. Il n'appelle jamais `enqueue`, `claim`, `heartbeat` ou `finish`.
Aucun job réel ou base de MAIN n'est modifié. Les tests utilisent un SQLite
synthétique sous le répertoire temporaire système, à configurer sur MAIN sous H:\temp.

Les garanties de livraison de messages, retries, claim/lease/fencing durables,
arbitrage GPU, réponse distante et acquittement restent **hors périmètre**.
Le contrôle de génération en lecture ne constitue pas un fencing d'exécution.

Le lot suivant devra étudier un transport Messenger durable réellement lié au
registre canonique, sans créer de deuxième queue et sans activer de worker sans
preuve de sécurité et recette de non-régression.
