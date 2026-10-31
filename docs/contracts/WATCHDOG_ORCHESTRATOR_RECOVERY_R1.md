# Watchdog / Orchestrator - contrat de reprise R1

- Le watchdog Windows est autonome vis-a-vis de Symfony et de l'etat `pending`.
- Au boot : Caddy DEV, Caddy PROD et FastCGI ROOT (8791).
- Les deux Caddy sont observes exclusivement via HTTP : DEV 8790, PROD 8501.
- Une reponse HTTP quelle que soit sa classe (y compris 502 et 503) signifie que Caddy repond. Les backends sont du ressort de l'Orchestrator.
- Caddy absent : demarrage direct. Caddy present et non repondant depuis au moins 60 s : arret du seul processus identifie (executable + commande + configuration), puis relance.
- Port occupe par une autre instance : aucune terminaison, journaliser et poursuivre l'autre cible.
- Les pannes DEV et PROD ne se bloquent pas mutuellement. Les erreurs ne se transforment jamais en validation positive.
- FastCGI ROOT est lance quand 8791 est libre et qu'aucun processus ROOT identifie n'existe ; si un processus existant ne repond pas, la remise en etat est signalee, sans terminaison aveugle.
- L'Orchestrator pilote les autres FastCGI et workers selon leurs etats desires, sans superviser ses propres Caddy.
- Pas de nouveaux scripts permanents, pas de tests PHPUnit au boot, pas de mutation de la configuration des taches Windows a l'installation.
- Recette principale : terminer Caddy DEV puis PROD et verifier leur retour HTTP au cycle de surveillance ; controler aussi la conservation du domaine sain.

## Limites de ce lot

Le programme de supervision FastCGI applicative Symfony est conserve et devra etre simplifie dans un lot separe. Le script de tache existant continue de referencer 4.2c64 pour certaines operations : ne pas executer son action Update avant correction. La tache planifiee demeure desactivee apres installation jusqu'a activation explicite de l'operateur.
