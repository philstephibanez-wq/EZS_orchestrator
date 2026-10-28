# 4.2c5 — Layout partagé et sonde GPU

Capture MAIN : page /jobs accessible mais sans bandeau marque/version ni sonde GPU. Cause : page jobs HTML autonome, sans inclusion de _gpu_monitor et du script de télémétrie.

Correction : `templates/layout/base.html.twig` unique pour header, version DEV, sonde GPU, navigation et scripts partagés ; les vues Infrastructure et Jobs héritent de ce layout et conservent chacune leur contenu. Les scripts spécifiques Infrastructure restent limités à cette vue. Même composant GPU et même endpoint `/api/v2/gpu/dashboard` sur les deux pages, sans duplication de sondes.

Contrôleurs : version canonique et page active transmises explicitement. Aucun changement /api/jobs, worker, GPU backend, PROD ni cycle START/STOP.

Test statique ajouté ; contrôle navigateur demandé : page Infrastructure et /jobs doivent afficher header, version 4.2c5, panneau GPU et liens identiques ; absence d'erreur JS. Aucun test MAIN encore exécuté.
