# EZS queue — observation Windows 4.2d20

## Objet

`WindowsExecutorObservation` transforme l'inventaire Windows existant en une observation d'identité strictement locale et en lecture seule. L'instance est construite explicitement avec `WindowsProcessInventory` et le nom de noeud attesté ; aucun service n'est lancé automatiquement.

## Sémantique de sécurité

- Le PID doit être positif et appartenir au noeud local attendu.
- Le PID et la date native de création WMI doivent correspondre exactement à l'identité inscrite lors du claim. Aucune conversion de format implicite.
- Une identité correspondante fournit `running_confirmed`, ce qui **interdit** la récupération.
- PID absent, PID réutilisé, inventaire incomplet, noeud distant, droits insuffisants, erreur WMI ou preuve de descendants manquante : `unknown` et récupération **interdite**.
- Cette sonde ne renvoie **jamais** `stopped_confirmed` : l'absence d'un PID ne démontre pas l'arrêt de son arbre de processus.
- `ExecutorStopAttestor` et `TrustedLeaseRecovery` restent propriétaires de la décision : ils exigent une attestation positive indépendante pour récupérer.
- Aucune terminaison, adoption ou création de processus ; aucun accès en écriture à SQLite ; aucune route HTTP ; aucun scheduler ni worker permanent.

## Étude d'impacts

| Domaine | Avant | Après | Risque et prévention | Validation / retour arrière |
|---|---|---|---|---|
| Coordination | Attestor avec callback injecté | Adaptateur explicite à WMI | Les PIDs manquants ne prouvent pas l'arrêt ; retour `unknown` | Tests synthétiques ; retirer l'adaptateur, sans changement de schéma |
| Windows MAIN/XPS | Inventaire WMI en lecture seule | Même inventaire réutilisé | Droits COM / timestamp ; fail closed | Test avec provider injecté ; pas de sonde activée par défaut |
| PROD / ROOT / FastCGI | Invariant | Invariant | Aucune route, aucun démarrage, aucun arrêt | lint:container, tests complets, contrôle Git |
| CPU / GPU / mémoire | Aucun balayage actif | Aucun balayage actif | Pas de tâche périodique ; aucun surcoût sans appel explicite | Inspection du conteneur et du diff |

## Limites et suite

Ce composant ne prouve pas la fin d'un groupe de processus après crash et ne rend pas la récupération automatique opérationnelle. La prochaine étape devra apporter une preuve durable et indépendante de la fin **de l'intégralité de l'arbre de processus**, avec tests de panne contrôlée et observation réelle Windows sur un job exclusivement synthétique. Aucun appel aux jobs réels ou GPU n'est autorisé par ce contrat.
