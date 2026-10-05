# EZS Orchestrator V1.0.8a — UX déploiement

Baseline stable validée.

- Console de progression live du déploiement
- État À JOUR quand DEV == PROD
- Historique lisible avec message et auteur du commit
- SHA court conservé pour la traçabilité
- Composer/Symfony forcés en APP_ENV=prod et APP_DEBUG=0

Pipeline validé : DEV → préflight → maintenance PROD → backup DB → git fast-forward → Composer → Doctrine → cache → restart → health check → sortie maintenance → restauration worker.

