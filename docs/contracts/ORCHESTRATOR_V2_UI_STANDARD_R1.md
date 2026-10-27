# UI V2 — premier écran standardisé (1.3b8)
- Twig et Bootstrap 5.3.3 pour le rendu. jQuery 3.7.1 pour actualisation non-mutante du catalogue REST. Scripts isolés sous `web/public/assets`, pas de JavaScript dans le template.
- Aucune action d'exécution ; l'API GPU reste protégée par token, non exposée au navigateur.
- Le catalogue SSR continue d'être affiché même si le JavaScript ou le CDN est indisponible ; le bouton affiche une erreur de rafraîchissement si l'appel échoue.
- CDN épinglé pour cette première étape de test ; distribution statique locale et CSP restent à valider avant production. Ne pas modifier les versions jQuery de LAB/Assistant sans tests de leurs plugins.
- L'ancienne page Twig est remplacée dans le même commit, pas d'écran parallèle. Ne pas supprimer le Control Center Python avant parité complète.
- Tests MAIN : `php web/tests/UiStandardTest.php`, `php web/bin/console lint:twig web/templates`, `php web/bin/console lint:container`, `php web/bin/console debug:router`. Test de rendu navigateur via Caddy encore à réaliser.
