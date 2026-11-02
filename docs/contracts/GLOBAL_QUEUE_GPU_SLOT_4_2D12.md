# 4.2d12 — Exclusivite GPU transactionnelle

Le registre canonique `GlobalQueueStore` refuse un nouveau `claim('gpu')` lorsqu'un job GPU est deja `running`, quelle que soit sa provenance. Le controle est realise sous le meme `BEGIN IMMEDIATE` que le claim ; les appels CPU restent independants.

Un lease GPU expire mais encore `running` **continue a bloquer** le slot. Aucune recuperation implicite ni execution distante n'est autorisee avant une procedure de fencing / attestation de non-execution separee. Ce changement garantit l'exclusivite de claim au sein du registre, **pas** une preuve d'exclusivite de tous les processus GPU etrangers ou une reprise apres crash.

Aucun worker Messenger, transport, endpoint REST, polling, migration SQLite ou demarrage de service n'est ajoute. Aucun job reel n'est reclame par l'installation ou les tests. Les tests executent des bases SQLite synthetiques isolees dans un dossier temporaire.

Recette MAIN: PHP lint, Composer validate, lint:container, test cible `GlobalQueueGpuSlotTest`, suite PHPUnit complete, controle de l'encodage UTF-8 sans BOM, git diff --check. Le fonctionnement de la queue avec des producteurs reels reste non valide.
