# Handoff — Publication terminale ONE SHOT V2 — 27/10/2026

## Décision
L'Orchestrator **Symfony/PHP** reçoit de LAB et Assistant les confirmations finales, regroupe/normalise leurs comptes rendus expurgés selon les événements métier autorisés et publie sur le dépôt privé `philstephibanez-wq/EZStudio_Run_Reports` **une fois à la clôture**, sans polling ni reporting périodique.

## États
LAB analyse finalisée et/ou Assistant contre-expertise finalisée → validation de terminalité + corrélation/idempotence → outbox persistante Symfony → Messenger publisher → GitHub private commit → vérification retour + SHA/état `published`.

Si un rapport consolidé doit inclure à la fois analyse et expertise, ne pas publier avant que les deux soient finales. Échec d'envoi : rejouer **la publication seule**, jamais le traitement scientifique. Rapport expurgé, authentification minimale, sans secrets/audio/éléments bruts.

## Références / non-régression
- Contrat : `docs/contracts/ORCHESTRATOR_V2_PRIVATE_REPORTS_ONESHOT_2026_10_27.md`
- Issues : #18 et #15.
- Ancien `scripts/publish_jobs_report.py` = snapshot de queue et publication rolling ; ce n'est **pas** le contrat demandé et sera retiré à la bascule après audit.
- Aucun worker ou service démarré, aucun job existant consommé ; statut **contrat uniquement**.

## Exception bootstrap initial : start
Le seul point d'entrée autorisé hors du runtime PHP/Symfony est le **bootstrap initial `start`**, nécessaire lorsque le serveur et Symfony ne sont pas encore actifs. Il peut s'agir d'un lanceur Windows minimal et stable. Cette exception ne permet ni logique de queue, ni Git, ni déploiement, ni supervision parallèle, ni deuxième cycle de vie. Après initialisation, PHP/Symfony reprend intégralement le contrôle des opérations d'orchestration. Aucun double démarrage, singleton et ownership obligatoires. La forme exacte du lanceur sera qualifiée avant implémentation.

## Exception explicite — sondes techniques
Les **sondes** sont également autorisées comme exécutables/outils techniques externes à PHP, lorsqu'une mesure native l'exige (ex. GPU MAIN). Symfony reste l'autorité qui les déclenche, supervise, contrôle leurs délais et exploite leurs résultats ; aucune sonde n'administre l'Orchestrator ni ne possède une file autonome. Une sonde commune MAIN évite les duplications LAB/Assistant. Cette exception complète celle du seul bootstrap initial `start` et ne réintroduit pas des scripts d'orchestration Python ou PowerShell.

## Critère bloquant Windows 11 : aucune fenêtre console visible
Aucun flash de fenêtre CMD, PowerShell ou console n'est acceptable au bootstrap `start`, avec Git, sondes natives, Caddy/PHP, queues Messenger, deploy/restart/diagnostics, ni lors des erreurs. Le bootstrap externe minimal et les sondes sont des exceptions à l'implémentation interne Symfony, **pas** au critère d'invisibilité. Processus enfants pilotés par Symfony, sans wrappers CMD/PS, avec mode no-window Windows attesté en recette réelle (ne pas présumer que `start /B` ou masquer une fenêtre après apparition suffit). Zéro vol de focus. Recette interactive Windows 11 : lancements répétés, Git, sondes, incidents et redémarrages ; 0 apparition de console. Garder état courant sans activation pendant la documentation.
