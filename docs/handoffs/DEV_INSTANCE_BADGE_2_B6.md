# v2.b6 — badge DEV EZScore

GitHub EZScore/templates/base.html.twig affiche le badge si et seulement si app.request.server.get('EZSCORE_INSTANCE') vaut 'dev'. Les commandes PHP Symfony sur MAIN montrent APP_ENV=dev, mais elles ne prouvent pas EZSCORE_INSTANCE dans la requête FastCGI. Le lanceur v2.b5 démarre les backends 8602/8862 sans définir cette variable.

Correctif ciblé : start.ps1 exporte EZSCORE_INSTANCE=dev avant Start-Process PHP-CGI, sans toucher au projet EZScore, à son template, à ses données ni au SSO Google. Les processus déjà présents ne reçoivent pas la nouvelle variable : la recette doit inclure un arrêt contrôlé du cycle DEV, qui conformément au contrat provoque d'abord une maintenance PROD. Ne jamais tuer manuellement les PIDs et ne pas supprimer l'état.

Test statique : php tests/DevInstanceBadge2B6ContractTest.php. Validation live du badge **non effectuée** avant publication ; reproduire avec stop.ps1 puis start.ps1 dans la fenêtre de maintenance acceptée, confirmer page 8502, badge rouge, session et SSO. La preuve que les répertoires MAIN H:/EZScore et H:/EZScore_dev contiennent exactement les versions GitHub reste à recueillir.
