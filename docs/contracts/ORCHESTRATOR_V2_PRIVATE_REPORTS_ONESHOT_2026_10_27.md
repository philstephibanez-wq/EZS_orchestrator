# ORCHESTRATOR V2 — Publication événementielle ONE SHOT des résultats

Décision : 27/10/2026. Statut : contrat cible, **non implémenté**.

## Autorité et destination
- Orchestrator Symfony/PHP porte seul le transport et la publication de synthèses expurgées vers le dépôt GitHub **privé** `philstephibanez-wq/EZStudio_Run_Reports`, uniquement après confirmation de fin de traitement par le composant propriétaire.
- LAB produit les résultats d'analyse PROFILE/STEMS/CHORDS-N/LYRICS ; Assistant produit la contre-expertise des assertions musicales finales, dans le périmètre autorisé. Orchestrator ne calcule, ne valide et ne modifie aucun résultat scientifique.
- Les données canoniques de traitement demeurent chez leur producteur ; le dépôt privé contient des rapports de preuve/traçabilité **sanitisés**, pas des fichiers audio, modèles, prompts secrets, tokens ni données brutes sensibles.

## Événement de clôture et sémantique ONE SHOT
- Une publication **par événement terminal confirmé et version de résultat** : analyse terminée, expertise terminée, ou dossier consolidé lorsque le contrat métier confirme que toutes les étapes requises sont finales. Ne pas publier d'état intermédiaire, de snapshot périodique ni de lot d'historique.
- Si une chaîne analyse → contre-expertise exige un **rapport consolidé unique**, attendre la fin confirmée de toutes ses étapes ; distinguer explicitement les événements indépendants si un rapport par traitement est requis. Aucun commit avant le terminal réellement vérifié.
- Clé de déduplication stable : composant + run_id + type d'événement + version/révision. Une nouvelle révision finale donne un nouvel événement ; la répétition du même callback ne crée pas de second commit.
- Persisted outbox Symfony transactionnelle + Messenger : `pending → publishing → published` ou `retryable_error/terminal_error`. Retry borné, reprise crash et backoff ; un échec GitHub ne réexécute **jamais** l'analyse ou l'expertise.
- GitHub : identité de dépôt et branche explicites ; permissions minimales et secret hors Git ; compare-and-swap/version du fichier ou commit atomique, preuve de lecture après écriture, hash du payload et SHA Git du commit conservés. Après timeout ambigu, vérifier l'existence de l'artefact cible avant retry.

## Schéma minimal à contractualiser
`schema_version`, `publication_id`, `event_kind`, `producer`, `target_environment`, `run_id`, `correlation_id`, `final_status`, `completed_at_utc`, `source_revision`, `provenance`, `summary_sanitized`, `expertise_status` (si applicable), `published_at_utc`, `content_sha256`.

Pas de dumps de files, aucune fuite d'information à travers un dépôt privé, pas d'écrasement silencieux d'un événement distinct. Chaque champ métier est fourni par sa source, non inféré par l'Orchestrator.

## Recette / gates
1. Fin métier validée via REST authentifié et corrélation ; aucune publication en `queued/running`.
2. Deux callbacks terminaux identiques ⇒ un seul artefact logique/commit ; crash avant/après push ou ack ⇒ reprise idempotente.
3. Échec réseau/auth/permissions ⇒ état erreur visible, retry publication seulement, pas de nouveau job scientifique.
4. Deux fins simultanées ⇒ deux rapports distincts, aucun lost update.
5. Rapport expurgé validé et lecture retour vérifiée ; journaux sans secrets.
6. Aucun polling périodique, aucune tâche Windows, aucun script Python/PowerShell de publication ; suppression de `scripts/publish_jobs_report.py` uniquement après substitution validée et audit de ses dépendances.
7. Jobs existants #181/#182/#185 : aucune consommation ni clôture à des fins de recette.

## Handoff
Implémenter sous modules Symfony dédiés (événements terminaux, outbox, Messenger, GitHub publisher, observabilité), pas en CLI ponctuelle. L'issue #18 pilote la migration et #15 le trajet LAB/Assistant. Maintenir les chemins encore actifs jusqu'à une bascule prouvée.


## Exécution système — règle V2 irrévocable
Toutes les opérations d'orchestration, y compris Git, sont implémentées en services **PHP 8.5 / Symfony**. Les binaires tiers (`git.exe`, `caddy.exe`, `php-cgi.exe`, etc.) sont exécutés directement par PHP avec arguments structurés (p. ex. `proc_open()`), contrôle d'identité, autorisations, ownership PID, environnement, timeout, sortie, code retour et journalisation expurgée. **Aucun wrapper/script Python, PowerShell, Bash ou CMD** dans les opérations internes une fois Symfony démarré ; exception explicite : bootstrap initial `start` hors application. L'utilisation de `git.exe` ne signifie pas réimplémenter Git en PHP. Les anciens scripts sont inventoriés puis supprimés lors de la bascule validée, sans interruption prématurée des services.

## Exception bootstrap initial : start
Le seul point d'entrée autorisé hors du runtime PHP/Symfony est le **bootstrap initial `start`**, nécessaire lorsque le serveur et Symfony ne sont pas encore actifs. Il peut s'agir d'un lanceur Windows minimal et stable. Cette exception ne permet ni logique de queue, ni Git, ni déploiement, ni supervision parallèle, ni deuxième cycle de vie. Après initialisation, PHP/Symfony reprend intégralement le contrôle des opérations d'orchestration. Aucun double démarrage, singleton et ownership obligatoires. La forme exacte du lanceur sera qualifiée avant implémentation.

## Exception explicite — sondes techniques
Les **sondes** sont également autorisées comme exécutables/outils techniques externes à PHP, lorsqu'une mesure native l'exige (ex. GPU MAIN). Symfony reste l'autorité qui les déclenche, supervise, contrôle leurs délais et exploite leurs résultats ; aucune sonde n'administre l'Orchestrator ni ne possède une file autonome. Une sonde commune MAIN évite les duplications LAB/Assistant. Cette exception complète celle du seul bootstrap initial `start` et ne réintroduit pas des scripts d'orchestration Python ou PowerShell.
