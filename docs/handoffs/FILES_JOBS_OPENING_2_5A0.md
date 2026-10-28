# Ouverture de Files & Jobs v2.5a0
Base stable : 2.4b START/STOP validée sur MAIN, intangible pour cette ouverture.
Sources transversales lues : Orchestrator #8 #15 #18, ExclusiveLease ; LAB #16 R3B6, LabJobStore et DistributedAnalysisLeaseService ; Assistant #5 et profile_worker_supervisor ; EZScore AnalysisJobManager.
Nouvelle issue : #19. Étape suivante : audit du code historique V1 et matrice état/attempt/persist/claim/lease/ack/retry/annulation/observabilité avant tout moteur.
Limites : ni Messenger ni worker lancé, ni queue ou job modifié ; jobs LAB 181/182/185 protégés ; recette PROD #8 non terminée ; pas de changement runtime ou science.