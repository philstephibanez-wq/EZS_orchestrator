# EZS WEB ONLY R8 — 4.2d69

## Décision
Le lancement des sites est une seule opération plateforme à l'initialisation du résident ROOT.
Aucune commande individuelle Démarrer/Arrêter/Redémarrer n'est accessible depuis Infrastructure.
La disponibilité web est définie par les ports TCP et le statut HTTP de la page publique locale ; aucun test de PID/ownership ni appel aux endpoints REST métier.
Le seul contrôle utilisateur PROD reste Normal / Maintenance via `ProdModeService` existant.

## Ports et pages
- DEV : 8502,8602 ; page `/fr/catalog`
- LAB : 8702,8701 ; page `/`
- Assistant web : 8712,8713 ; page `/` ; Llama 8720 ne conditionne pas le démarrage web.
- PROD : 8501,8510,8511 ; page `/fr/catalog` ; en mode Maintenance, 8501/503 est attendu.

## Risques et sûreté
- Si un seul des ports d'un site est occupé, le bootstrap ne lance pas de deuxième processus concurrent et n'arrête rien. L'état PARTIAL est affiché, pas corrigé automatiquement.
- DEV hérite temporairement de `EZSCORE_MEDIA_ROOT` canonique `H:\EZScore_dev\var\storage\stems` uniquement pour sa commande de lancement.
- Le lancement PROD conserve exclusivement son adaptateur canonique interne, nécessaire à la bascule sûre vers `EZS_maintenance` ; il n’intervient pas dans le ping hard et ne devient pas un contrôle individuel utilisateur.
- Le serveur Assistant web est lancé directement via le `Caddyfile.assistant.native` publié par Orchestrator : **pas** d'appel au lanceur couplé Web + Llama, ni de modification du dépôt Assistant.
- Le mécanisme de bascule maintenance existant conserve ses dépendances et limites ; aucun processus PROD n'est arrêté par le bootstrap.
- Le bootstrap est tenté une fois au démarrage du résident après santé ROOT, pas lors d'un rafraîchissement de page.

## Migration / legacy
Le nouveau parcours web n'appelle plus les anciennes commandes individuelles. Les anciens composants internes requis par les contrats historiques restent conservés et doivent être retirés après audit de leurs appelants (notamment maintenance R6B et tests historiques). **Le nettoyage physique complet n'est pas réalisé par cette révision.**

## Validation
Contrôles de syntaxe PHP et archive en environnement de préparation ; suite PHPUnit complète et démarrage Windows à exécuter sur MAIN. Pas de validation d'accessibilité réelle hors MAIN.
