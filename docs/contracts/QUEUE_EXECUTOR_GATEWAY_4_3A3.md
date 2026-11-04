# Orchestrator 4.3a3 — Passerelle REST d'exécuteur (inactive)

## Décision et non-duplication

Le registre existant `GlobalQueueStore` est l'unique autorité des états techniques. La nouvelle passerelle REST réutilise ses méthodes `claim()` (transaction `BEGIN IMMEDIATE`, slot GPU unique), `heartbeat()` (lease courant et progression monotone) et `byId()`. Aucun scheduler parallèle, transport Messenger, worker ou processus enfant n'est créé. La table SQLite canonique et les formats existants sont conservés.

Cette livraison est **un protocole d'accès, pas une mise en exploitation**. Elle ne fournit pas de moteur d'exécution, de preuve de démarrage/arrêt du groupe de processus, de callback métier LAB, de confirmation de persistance, ni de mécanisme de finalisation sécurisée. En conséquence, **aucune route de succès/completion n'est créée**. Les anciens jobs LAB (#181, #182, #185 et #193–#198 au dernier inventaire) restent sous l'autorité LAB et ne sont pas migrés.

## Routes dormantes

- `POST /api/v2/queue/executor/claim` : JSON exact `{ "resource_class": "gpu|cpu", "lease_seconds": 30..600 }`; renvoie `job=null` lorsqu'aucun job n'est disponible, sinon identité technique et secret de lease au seul exécuteur authentifié. Le secret de lease ne doit être ni loggé ni retourné aux producteurs ou aux interfaces.
- `POST /api/v2/queue/executor/heartbeat` : champs exacts `job_id`, `claim_generation`, `lease_token`, `lease_seconds`, `progress_percent` (`null` ou entier 0..99). Réponse sans secret, `409` si génération/lease périmé.
- Gate **fermée par défaut** : `EZS_QUEUE_EXECUTOR_API` doit être exactement `1`, plus jeton distinct `EZS_QUEUE_EXECUTOR_TOKEN` de 32 à 256 caractères dans l'environnement natif ou Symfony. Aucun fichier `.env.local` n'est ouvert par la passerelle ; aucun secret executor n'est fourni par ce ZIP.
- Le pair TCP direct doit être loopback ; les en-têtes forwarded sont ignorés. Sans gate : `404` avant toute ouverture de SQLite. Sans token dédié : `401`. JSON strict 2 KiB maximum. Pas de redirection ni de log de secret ; réponses `no-store`.
- `EZS_QUEUE_LAB_TOKEN` reste strictement le jeton de **producteur** et ne doit pas autoriser un claim d'exécuteur.

## Étude d'impact

| Avant | Après | Risque | Prévention et preuve | Retour arrière |
|---|---|---|---|---|
| Pas de routes executor | Deux routes dormantes uniquement | Claim accidentel | Gate absente et secret non provisionné ; test 404 sur MAIN, queue inchangée | Restaurer VERSION et retirer nouveaux fichiers avant publication |
| Claim interne non exposé | Accessible uniquement à exécuteur explicitement habilité | Usurpation / fuite de lease | Credential distinct, pair TCP direct, réponse `no-store`, filtres stricts, tests 401/403/422 | Retirer le flag avant tout retrait de code |
| GPU global transactionnel | Même store sans duplication | Double allocation | Tests fixture SQLite : deux jobs GPU, seul le premier peut être `running` | Aucun changement de store/DB |
| LAB `analysis_jobs` isolé | Inchangé | Données historiques | Aucune requête LAB ni POST positif dans installation/tests MAIN | Sans objet |
| FrankenPHP partagé DEV/LAB/PROD | Identique, pas de restart | Perturbation exploitation | Aucune commande de service, port ou processus ; PHP source uniquement | Restaurer code selon garde-fous |

## Bloqueurs avant exploitation

1. Implémenter le lanceur de confiance, l'attestation d'identité durable de processus et des descendants ; établir les permissions et la gestion de l'arrêt.
2. Définir l'ack LAB de **résultat effectivement persisté** avant `finish(success=true)` ; distinguer erreur scientifique et erreur de finalisation.
3. Requalifier Symfony Messenger (livraison de messages) sans deuxième état canonique et fiabiliser retry/ded-letter.
4. Tester sur bases SQLite synthétiques, puis recette de bout en bout expressément autorisée ; pas de revendication de fonctionnement réel avant cela.
5. Ne pas activer `EZS_QUEUE_EXECUTOR_API` ni `EZSTUDIO_GLOBAL_QUEUE_ADMISSION` avant ces preuves. Pas de claim de job réel, pas de redémarrage FrankenPHP.

## Recette

Préflight version `4.3a2`, HEAD Git exact, dépôt propre, fichiers nouveaux absents, SHA de VERSION ; puis apply sauvegarde VERSION sous `H:\temp` et installe uniquement des fichiers durables. Exécuter `php -l`, test ciblé `QueueExecutorGateway4_3A3Test.php`, suite PHPUnit complète, `lint:container`, `debug:router`, `git diff --check`. Vérifier que l'API avec gate absente renvoie 404 et que la queue MAIN est inchangée. Ne jamais appeler de POST de claim **valide** sur MAIN. Publication Git par le mainteneur uniquement après recette.
