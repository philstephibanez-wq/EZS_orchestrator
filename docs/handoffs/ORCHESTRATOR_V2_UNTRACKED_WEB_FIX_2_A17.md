# v2.a17 — absence de source legacy distincte des résidus ignorés

Le retrait Git v2.a16 est confirmé (aucun chemin web/ suivi). Sur MAIN, git pull ne supprimera pas nécessairement web/vendor, web/var et les secrets locaux ignorés. Le test v2.a16 refusait is_dir(web) et aurait donc échoué malgré la disparition effective des sources.

Le test distingue maintenant la présence de fichiers applicatifs de web/ de simples résidus ignorés. L'opérateur doit inspecter ces résidus avant tout nettoyage manuel ; aucune purge automatique. Les autres gates de Caddy root et Symfony ne changent pas. Tests Windows MAIN non exécutés à publication.
