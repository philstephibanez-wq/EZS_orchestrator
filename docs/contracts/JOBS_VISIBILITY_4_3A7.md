# Contrat Jobs Visibility 4.3a7

## Objet

Afficher les jobs des sources existantes dans `/jobs` sans créer une file supplémentaire.

- **Queue globale Orchestrator** : état canonique des jobs admis, `running` historique conservé, indicateur `lease_expired` dérivé de l'horodatage de bail. Affichage en lecture seule, sans récupération ni claim.
- **Queue LAB** : réemploi de `LabQueueProbe` via REST LAB, vue *déclarative du producteur* ; elle ne possède pas l'autorité de claim GPU. Si LAB est indisponible, afficher cette indisponibilité, sans inventer des jobs.
- **Archives V1** : continuer d'afficher les snapshots `result.json`, explicitement séparés des jobs courants.
- **Actualisation** : navigation GET toutes les 15 s uniquement lorsque l'onglet est visible ; aucun worker ni processus démarré par ce mécanisme.

## Non-régression

Aucun changement de `GlobalQueueStore`, `GlobalQueueProfileBridge`, SQLite, migration, API d'admission, Assistant, moteur scientifique, mode PROD, script de boot ou secrets. Le probe LAB réutilise l'API existante et le token interne en mémoire, jamais affiché. Une indisponibilité HTTP LAB n'empêche pas la queue globale de rester visible.

## Limites et validation

- Le nombre de lignes est borné à 100 par source, sans import des jobs LAB dans la queue globale.
- Un bail expiré n'est pas la preuve que l'exécuteur ou ses descendants ont arrêté ; aucune transition automatique n'est autorisée.
- Tests PHP : syntaxe, contrat de séparation des sources, lecture SQLite synthétique, absence de mutation.
- Recette MAIN : PHPUnit, Symfony, Twig, GET `/jobs`, vérification visuelle des jobs LAB et de l'alerte #202. Le résultat HTTP de LAB dépend de son API existante et de son token ; il n'est pas attesté hors MAIN.
- Le livrable n'effectue aucun recovery du job #202 et ne prétend pas achever la migration de Messenger.

## Retour arrière

L'installateur conserve chaque fichier d'origine sous `H:\temp\EZS_JOBS_VISIBILITY_4_3A7_BACKUP_*` et fournit `rollback` explicite. Restaurer seulement après arrêt des opérations modifiant les mêmes fichiers. Ne jamais supprimer les preuves du job #202.
