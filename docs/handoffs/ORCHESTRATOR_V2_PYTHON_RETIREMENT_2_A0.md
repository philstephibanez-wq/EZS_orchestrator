# EZS_orchestrator v2.a0 — migration des fichiers Python (27 octobre 2026)

## Objectif non négociable
À terme aucun fichier .py, invocation Python ou logique de queue Python dans EZS_orchestrator. Toute l'administration, le cycle de vie, les commandes système (Git compris), les queues Messenger et le reporting ONE SHOT sont gérés par PHP/Symfony. Exceptions externes limitées au bootstrap start et aux sondes natives, sans console Windows 11 visible. Les workers scientifiques des applications restent hors du dépôt Orchestrator.

## Inventaire de départ
169 fichiers .py sur master avant cette livraison, dont modules de production et suites de tests. Ne pas confondre suppression de fichiers avec migration fonctionnelle. Pas de suppression des systèmes de queue, supervision ou PROD avant validation et bascule.

## Lot isolé v2.a0
- VERSION = 2.a0.
- Ajout de web/src/Module/Infrastructure/ProdFastcgiPreflight.php : préflight PROD candidat en lecture seule, configuration, racines, Caddyfile, maintenance et ports 8511/8512.
- Ajout de web/tests/ProdFastcgiPhpCandidateContractTest.php : assertions statiques d'isolation et de non-mutation.
- Les anciens prod_lifecycle/fastcgi_preflight.py et tests/test_prod_fastcgi_candidate.py ne seront supprimés **qu'après validation locale Windows et audit de tous leurs appels** : ne pas casser l'ancienne recette avant la preuve d'équivalence.
- Le NativeCommandRunner est un socle expérimental ; **ne pas supposer** zéro console sous Windows avant test interactif.
- Aucune route ni lifecycle PROD muté ; aucune queue consommée.

## Vérification Windows MAIN
1. git pull --ff-only origin master
2. Get-Content .\VERSION
3. & 'H:\PHP\php-8.5-x64\php.exe' -l .\web\src\Module\Infrastructure\ProdFastcgiPreflight.php
4. & 'H:\PHP\php-8.5-x64\php.exe' .\web\tests\ProdFastcgiPhpCandidateContractTest.php
5. & 'H:\PHP\php-8.5-x64\php.exe' -l .\web\src\Module\Infrastructure\NativeCommandRunner.php
6. & 'H:\PHP\php-8.5-x64\php.exe' .\web\tests\NativeCommandRunnerContractTest.php

Après recette PASS : recenser les références du préflight Python et remplacer la commande canonique par un point d'entrée PHP/Symfony ; retirer le Python et ses tests dans le **même lot de bascule**, sans supprimer les autres Python actifs. Ne pas remplacer un test de comportement par des tests statiques seuls.

## Séquencement
1. Isoler/porter/valider puis retirer préflights et diagnostics.
2. Propriétaires Windows native process, singleton et sonde GPU ; tests sans fenêtre visible.
3. Migration API/supervision, queues Symfony Messenger et persistance.
4. Transport Git et publication événementielle des résultats en fin confirmée de traitements.
5. Supprimer les Python et scripts legacy restants seulement avec équivalence attestée, puis gate automatisé zéro .py.
