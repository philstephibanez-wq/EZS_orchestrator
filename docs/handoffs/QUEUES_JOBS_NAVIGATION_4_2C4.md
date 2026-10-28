# 4.2c4 — Navigation Files & Jobs

Capture MAIN 4.2c3 : « Files & Jobs · en migration » inactif. Source GitHub `templates/infrastructure/index.html.twig` : navigation rendue par `<span>` au lieu d'un lien. Aucun contrôleur de page /jobs en place.

Correction : lien `/jobs` ; contrôleur Symfony `JobsPageController`, page Twig de suivi en lecture seule. Page sans fetch d'API, sans simulation d'historique, aucun worker/claim, aucun JS de jobs, aucune mutation. L'API héritée `/api/jobs` reste 503 explicite. Les éléments V1 seront réintroduits seulement après validation des contrats.

Recette demandée : test PHP, `php bin/console debug:router ezs_v2_jobs_page`, ouverture HTTP /jobs depuis façade 8790. Pas de changement de lifecycle 4.2b, PROD, LAB ni Assistant.
