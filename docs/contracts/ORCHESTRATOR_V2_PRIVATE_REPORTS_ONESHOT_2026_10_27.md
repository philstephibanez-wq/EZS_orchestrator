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
