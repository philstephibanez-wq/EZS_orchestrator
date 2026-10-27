# Correctif v2.a9 — MIME JS preview

Recette sur MAIN sous Caddy 8890 / FastCGI 8891 : le JavaScript GPU répond HTTP 200 et est chargé visuellement, mais le test v2.a8 échoue `ROOT_PREVIEW_HTTP_FAILED:/assets/ezs-gpu-monitor.js`. La condition recherchait le texte littéral `content-type: javascript`, alors que les types MIME valides sont `text/javascript` ou `application/javascript`.

Le correctif ajuste seulement la sonde de recette HTTP, accepte les deux types MIME JavaScript, conserve la vérification du contenu et signale le type réel en cas d'échec. Il refuse les réponses `text/html`, notamment la régression du routeur `php -S`. Aucune modification de Caddy, PHP-CGI, Symfony, GPU ou des quatre pavés.

Validation : lecture et revue statique des sources GitHub. À exécuter sur MAIN : `php -l tests/SymfonyRootPreviewProbeTest.php` et `php tests/SymfonyRootPreviewProbeTest.php`. La recette HTTP ne peut pas être certifiée à distance sans son résultat. Les limites fonctionnelles de la migration restent inchangées.
