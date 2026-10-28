# 4.2c3 — Registre durable jobs/attempts

GitHub V1 vérifié : `control_center/job_history.py` en parent `4b87f43a1b4a8293ee77421a007cfcc532ac2ebd` lit `runtime/jobs/{dev,prod,lab}/{job_id}/{run}/result.json` et `execution.log`. `transport/jobs.py` lit queue REST, obtient le verrou machine avant claim et libère après complete/fail. Les fichiers V1 constituent une **trace historique**, non une raison de réactiver Python.

Implémentation `JobRegistry` : SQLite local, WAL, contrainte d'identité `(target,job_id)`, tentatives `(target,job_id,attempt_no)`, transactions BEGIN IMMEDIATE, états projetés par `JobAttemptProjection`, transitions vérifiées, refus des répétitions contradictoires, séquence des tentatives contrôlée. Aucune création automatique de job distant, aucun lien REST ou Messenger. `PDO_SQLITE` requis.

**Restriction essentielle** : ce registre n'est pas encore l'autorité des claims distribués, ni une restauration complète des logs, identités d'executor, leases/expiration, priorités effectives, idempotency keys ou callbacks. Il n'est connecté à aucun service et ne doit pas être activé sur des jobs réels. Les états terminaux ne sont pas réécrits. START/STOP 4.2b inchangés, jobs LAB #181/#182/#185 intouchés.

Test autonome utilisant un fichier temporaire système (hors dépôt) ; à exécuter sur MAIN avec PHP. Tests concurrents et intégration à suivre.
