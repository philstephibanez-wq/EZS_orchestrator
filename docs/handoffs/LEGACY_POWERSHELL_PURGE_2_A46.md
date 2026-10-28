# v2.a46 — retrait des wrappers PowerShell DEV historiques

## Décision et portée

Suppression de trois sources historiques : `scripts/start.ps1`, `scripts/stop.ps1`, `scripts/v2_lifecycle.ps1`. Leur code demeure récupérable dans l'historique Git avant cette révision. Aucun processus n'est arrêté par le retrait de ces fichiers, aucune configuration PROD n'est modifiée.

**Rupture fonctionnelle explicite :** les opérations DEV `start`, `stop` et `repair` ne disposent pas encore d'un équivalent Symfony opérationnel. Les anciens points d'entrée qui invoqueraient ces scripts sont donc non fonctionnels et ne doivent pas être utilisés. Le service `DevLifecycle` reste en lecture seule et refuse toute mutation. Ne pas traiter cette suppression comme une certification de parité.

## Conditions de remise en service

Implémenter une gestion de processus Symfony qui prouve l'identité forte, la propriété des enfants et des listeners, les locks exclusifs, la non-destruction des services DEV/PROD non possédés et le rollback, avec tests Windows 11 sans apparition de console. Recette MAIN obligatoire avant démarrage/arrêt réel.

## Recette

`php tests/LegacyPowershellPurgeContractTest.php`
`php tests/DevLifecycleReadOnlyContractTest.php`
`php tests/DevOwnershipAssessmentContractTest.php`
`git ls-files '*.py' '*.ps1'` pour inventorier tout reliquat suivi. Ce dernier contrôle n'est **pas** une preuve acquise tant qu'il n'a pas été exécuté sur MAIN.

Versionner uniquement le test durable, le handoff, VERSION et les suppressions. Aucune tâche Windows, service, queue ou processus modifié.
