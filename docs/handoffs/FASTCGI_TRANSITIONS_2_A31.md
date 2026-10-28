# 2.a31 — capture explicite des transitions FastCGI

Commande PHP : `php bin/infrastructure.php observe-fastcgi`. Une invocation recueille le PID mémorisé, le PID d'écoute et le nom d'image ; conserve le dernier échantillon et journalise les changements dans `%TEMP%/ezs-orchestrator/fastcgi-observations.jsonl` avec verrouillage et écriture atomique du snapshot. Ne lit ni ne supprime de processus ; aucun PS1/CMD supplémentaire.

**Limite majeure** : commande ponctuelle, pas de supervision autonome ; les heures sont celles des observations, pas des décès. Exécuter une fois à présent et après un incident. Une collecte périodique PHP devra être spécifiquement déployée pour tracer les disparitions entre deux consultations. La cause initiale du stop FastCGI n'est pas prouvée.

`infrastructure_restore.ps1`, `prod_lifecycle.ps1`, `v2_lifecycle.ps1` restent nécessaires tant que leur migration / essais de redémarrage à froid / conservation PROD ne sont pas finis.
