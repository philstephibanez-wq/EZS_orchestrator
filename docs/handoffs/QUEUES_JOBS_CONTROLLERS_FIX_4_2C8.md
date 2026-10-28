# 4.2c8 — Correctif de chargement des contrôleurs historiques

MAIN 4.2c7 : `php -l LegacyReadOnlyController.php` et test 4.2c7 réussissent ; `LegacyHistoryReadOnly42C6ContractTest.php` échoue sur son **garde de version 4.2c6**, sans atteindre ses assertions. Capture HTTP /jobs : `ClassNotFoundError` sur `LegacyJobHistoryReader` dans le namespace `Ezs\\Web\\Module\\Coordination\\Controller`, dû à l'absence de `use` dans JobsPageController.

Corrections : import PHP explicite du lecteur dans le contrôleur de page ; garde de version historique assoupli à la série corrective 4.2c6+ pour éviter un faux échec mécanique ; garde de test contrôleur 4.2c7 adaptée à VERSION=4.2c8 ; nouveau test vérifiant les imports et la syntaxe des deux contrôleurs.

Limites : tests de compilation et de source ne remplacent pas la recette HTTP MAIN. Aucune activation de worker, claim ou job et aucun changement START/STOP, PROD ni Assistant.
