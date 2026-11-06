# File unique / un job actif — contrat partiel 4.3a8

Le présent lot corrige uniquement l'admission au claim dans le stockage canonique d'Orchestrator. Il ne constitue PAS la migration Messenger complète.

## Règles

- Admission inchangée et durable via `GlobalQueueStore::enqueue()`.
- Un seul job en `running` globalement, peu importe sa classe de ressource.
- La tête de file est le job `queued` de plus ancien `(created_at,id)`. La priorité existante reste stockée mais ne réordonne pas les jobs.
- Un executor présentant un autre `job_id` ou une autre classe reçoit `null` et ne dépasse jamais la tête de file.
- L'ancienne finalisation et le fencing du token restent inchangés. Après `completed` ou `failed`, la prochaine tentative de claim peut prendre le suivant.
- Un job `running` à bail expiré conserve le verrou tant qu'aucune récupération attestée n'a eu lieu. Aucun reset de #202 et aucune relance implicite.
- Les quatre états affichés à l'utilisateur restent Demandé / En cours / Terminé / Erreur, sans nouvelle classe GPU dans l'interface métier.

## Manque à livrer, explicitement hors périmètre

Le transport et le worker Symfony Messenger de coordination centrale, le routage LAB/Analyse/Assistant, les callbacks normalisés et l'activation de l'ordonnanceur permanent. Le lot ne crée **aucun** nouveau consommateur. Sans eux, les transitions automatiques ne sont pas encore prouvées de bout en bout.

## Risques et rollback

Un consommateur avec `resource_class=cpu` est bloqué si le job de tête requiert `gpu`, et réciproquement : comportement volontaire pour FIFO stricte, implique un dispatcher central multi-types pour le fonctionnement final. Ne pas activer ce changement dans l'écosystème live avant coordination avec les producteurs. Rollback par l'installateur, après arrêt intentionnel des consommateurs et contrôle du manifeste. Le rollback ne réconcilie pas l'état des jobs exécutés depuis l'application.
