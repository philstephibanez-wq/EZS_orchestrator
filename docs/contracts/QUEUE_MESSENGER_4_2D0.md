# EZS — Queues & Jobs : contrat de migration v4.2d0 (lot R1)

## Autorités actuelles, preuves et limites

- `GlobalQueueStore` est la queue SQLite canonique de coordination (`data/queue/global.sqlite`). Elle porte `global_queue_jobs` et `global_queue_events`, l'idempotence, les priorités, `BEGIN IMMEDIATE`, le claim atomique, le jeton et la génération de lease, les heartbeats et la finalisation.
- `JobRegistry` conserve des tentatives techniques distinctes et le statut `finalize_error` ; ne pas assimiler cette projection au transport Messenger.
- `QueueRestReadModel`, `QueueReadController` et `QueueEventStream` exposent uniquement une lecture filtrée par producteur ; ne pas leur attribuer de capacité de dispatch.
- Aucun consommateur Messenger actif n'est attesté sur `4.2c`. `composer.json` ne déclare ni Messenger ni Doctrine Messenger ni Symfony Lock. Ce lot n'installe aucune dépendance.

## Règles de la future intégration Symfony Messenger

1. **Un seul registre métier canonique : `GlobalQueueStore`.** Messenger servira de mécanisme d'acheminement/consommation technique ; il ne doit pas produire une seconde vérité de `queued/running/completed/failed`.
2. Documenter explicitement la transaction de création et de notification (outbox transactionnelle ou approche équivalente), afin d'éviter le job enregistré sans message ou le message sans job.
3. Les handlers reçoivent une référence immuable à un job canonique, pas une copie de son état métier ; relecture et claim atomique avant dispatch. Un message redélivré ne doit pas provoquer une nouvelle exécution du même job.
4. Un ack Messenger ne signifie pas succès du traitement distant. `COMPLETED` exige une finalisation applicative confirmée ; `FINALIZE_ERROR` reste distinct de l'échec du worker. Les états de coordination actuels ne portent pas `finalize_error` : la politique de projection doit être explicitée avant activation, pas bricolée.
5. Les leases expirés ne sont pas récupérés automatiquement par le noyau actuel : qualification de reprise/fencing obligatoire avant tout consommateur. Un ancien détenteur ne doit jamais finaliser après réattribution.
6. Protéger le GPU machine-wide entre DEV, PROD, LAB et expertise ; ne pas confondre lease du job et exclusivité de ressource. Aucune préemption brutale.
7. Séparer les types de jobs scientifiques des demandes d'expertise. Nouveau type canonique `expertise.profile`. Les anciennes références ne doivent pas être consommées ou modifiées sans protocole de migration vérifié.
8. Propriété métier des résultats dans DEV/PROD/LAB ; Assistant fournit une expertise, LAB la persiste. REST authentifié, correlation ID, idempotency key, secrets jamais dans logs ou payload public.
9. Préserver les données MAIN et les jobs LAB #181, #182 et #185. Aucun nouveau job PROD, aucun claim, aucun worker lancé lors des lots de préparation.
10. Ne pas modifier le watchdog ROOT ni la supervision v4.2c ; aucun rollback automatique. La recette d'un lot doit être complètement indépendante de la base MAIN.

## Réception du lot R1

- `VERSION=4.2d0` avec contrat écrit et tests PHPUnit stateless dédiés au comportement EXISTANT de la queue ; fichiers de test uniquement dans les dossiers temporaires du système et nettoyage ciblé.
- Tous les contrôles réalisés sont explicitement distingués des contrôles restant à effectuer sur MAIN ; aucune prétention de validation live ou de migration Messenger.
- Avant un lot qui installe Messenger : vérifier la disponibilité de `pdo_sqlite`, la configuration Composer, les versions des composants et l'impact du transport sur SQLite/Windows et sur les opérations de maintenance.

## Veille technologique officielle (à réévaluer avant activation)

- Symfony 7.4 Messenger : https://symfony.com/doc/7.4/messenger.html
- Doctrine transport Messenger : https://symfony.com/doc/7.4/messenger.html#doctrine-transport
- Symfony Lock : https://symfony.com/doc/7.4/lock.html

