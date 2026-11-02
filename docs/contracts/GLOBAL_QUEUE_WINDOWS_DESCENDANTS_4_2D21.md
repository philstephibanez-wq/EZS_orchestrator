# EZS — Descendants Windows et refus de récupération 4.2d21

## Objet

Étendre la sonde canonique `WindowsExecutorObservation` sans introduire un second moteur : exploiter les liens `ParentProcessId` déjà retournés par `WindowsProcessInventory`, en lecture seule.

## Comportement

- Un PID racine vivant et sa date de création exacte restent `running_confirmed`.
- Le PID racine absent mais un enfant direct ou indirect relié par la chaîne de parents observée devient `unknown` avec `possible_descendant_still_running`.
- Un PID réutilisé, un inventaire WMI incomplet, une généalogie cyclique ou des descendants non visibles demeurent `unknown`.
- **Aucun résultat `stopped_confirmed` n'est produit**. Une association via `ParentProcessId` seule ne prouve pas la propriété d'un descendant, en raison de la réutilisation des PID.
- `ExecutorStopAttestor` et `TrustedLeaseRecovery` demeurent inchangés. Aucun recovery automatique n'est activé.

## Étude d'impacts

| Domaine | Avant | Après | Risque et prévention | Validation / retour arrière |
|---|---|---|---|---|
| Observation Windows | PID racine seulement | Parentés directes et transitives visibles | PID réutilisé et parents disparus : refus par défaut | PHPUnit 4 tests ; restaurer le fichier de sonde sauvegardé |
| CPU | Balayage simple | Index par PID, marche bornée par cycle | Coût de lecture et parcours quadratique dans le pire cas, seulement à appel explicite | Tests boucle et inventaire ; aucun timer |
| Sécurité GPU | `unknown` si absence racine | `unknown` avec diagnostic descendant quand visible | Ne jamais transformer absence en arrêt confirmé | Assertions attestor refuse |
| DEV/LAB/PROD | Aucun appel automatique | Identique | Aucun service, route, schéma ou tâche planifiée modifiés | `lint:container`, suite complète |

## Limites opérationnelles

La preuve d'arrêt **de l'intégralité d'un groupe Windows** exige un mécanisme de propriété et de clôture fiable, tel qu'un Job Object Windows tenu par un superviseur indépendant, et des essais réels de crash. WMI seul ne fournit pas cette preuve. Le lot n'ajoute ni worker ni récupération. Ne pas autoriser de job GPU réel sur cette base.
