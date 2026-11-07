# Queue PROFILE — reprise contrôlée 4.3a17

Ce jalon n’introduit ni second ordonnanceur ni nouvelle queue. Les seuls jobs autorisés pour le script de recette sont global #9/LAB #204 et global #10/LAB #205. Le `run` vérifie l'état de chaque job et sa finalisation LAB avant d'avancer. L'incident d'un job doit arrêter la reprise et préserver ses preuves. Les jobs historiques #3 à #8 restent inchangés, hors de la fenêtre active configurée sur MAIN. Le consommateur Messenger n'est pas installé comme service permanent par ce jalon. Aucun traitement scientifique ou contrat PROFILE n'est modifié.
