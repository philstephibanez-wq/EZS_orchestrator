# 4.2d18 — Première exécution CPU synthétique à travers la queue canonique

`SyntheticCpuQueueRunner::runOne(Closure $execute)` utilise `GlobalQueueStore::claim('cpu')`, exécute une fonction fournie explicitement dans le processus appelant, transmet une progression par `heartbeat()`, puis termine par `finish()` ; une exception du callback provoque `finish(..., false)` si le lease est encore valide. Aucune donnée de résultat du producteur n'est conservée par ce composant.

**Sécurité :** cette classe n'est pas enregistrée comme service Symfony, n'a aucun appelant permanent, aucune route ni commande d'exécution, aucun timer, aucun worker et aucun transport Messenger activé. Elle ne réclame jamais de job GPU. Les tests utilisent exclusivement des bases SQLite synthétiques dans le dossier temporaire de MAIN, jamais `GlobalQueueLocation::path()`.

**Limite explicite :** l'exécution a lieu dans le même processus PHP, et non un processus Windows enfant ; la preuve d'identité Windows, l'attestation de groupe, le retry borné, l'activation du vrai consommateur et les tests opérationnels après panne restent à réaliser. Un dépassement de lease empêche la clôture ; ce lot ne fournit pas de heartbeat automatique pour un callback bloquant. Le composant ne doit pas être branché à des producteurs réels ou à un scheduler sans contrôle supplémentaire.

Impact : un fichier de service Symfony modifié pour exclure explicitement la classe ; aucun effet sur les services Windows, ROOT, FastCGI, watchdog, PROD ou la queue réelle. Aucun legacy supprimé faute de remplacement équivalent. Rollback : restaurer VERSION et services.yaml à partir des copies MAIN hors dépôt, retirer les trois nouveaux fichiers après vérification de leurs modifications locales, sans rollback automatique.

Recette : `php -l` pour deux fichiers, Composer, `lint:container`, ciblés, PHPUnit complet, contrôle manifeste ZIP et UTF-8 sans BOM, `git diff --check`, inspection du statut Git. Les tests ne démontrent pas un lancement Windows réel.
