# Nettoyage des lanceurs — v2.5a1

La stabilisation START/STOP v2.4b a été confirmée sur MAIN. Le chantier Files & Jobs est ouvert en v2.5a0. La capture du répertoire scripts a révélé un script provisoire de bascule Caddy conservé après application.

Inventaire contrôlé :
- `start.ps1` / `stop.ps1` : points d'entrée canoniques ; conservés.
- `v2_lifecycle.ps1` : gestion du backend Orchestrator et préservation du Caddy DEV partagé ; appelé par START/STOP, conservé.
- `lab-assistant.ps1` : cycle des backends LAB et Assistant, appelé par START/STOP ; conservé.
- `prod_lifecycle.ps1` : gestion de PROD, usages non exhaustivement audités, conservé par sécurité.
- `caddy-dev-lab-assistant-cutover.ps1` : script ponctuel de bascule v2.b9/v2.b10, plus appelé par START/STOP après bascule validée ; supprimé de HEAD.
- `CaddyLabAssistantCutover2B9ContractTest.php` et `CaddyLabMediaResolution2B10ContractTest.php` : tests statiques exclusivement liés à ce script supprimé ; supprimés ensemble.

La configuration Caddy DEV active et tous les contrats d'architecture sont inchangés. L'historique de bascule reste consultable dans Git et dans les handoffs ; aucune suppression physique dans les historiques ou les machines n'est effectuée par cette livraison. Pas de changement de la sémantique START/STOP v2.4b. Aucune intervention PROD, LAB, Assistant, EZScore, aucune queue ni job exécuté.

Audit des références à reprendre au moment de la consolidation Symfony : `prod_lifecycle.ps1`, gestionnaire Caddy DEV autonome et suppression des wrappers legacy uniquement lorsque l'équivalence est prouvée. Ne pas supprimer de script encore appelé.
