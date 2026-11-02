# 4.2d11 — Référence Symfony Messenger cohérente

Le schéma généré et suivi `config/reference.php` documente `messenger.enabled` avec la valeur par défaut `true` après l'installation de Messenger 4.2d8.

L'écart local observé et vérifié sur MAIN depuis 4.2d8 est un remplacement strictement limité à un commentaire : `Default: false` → `Default: true`. Le fichier complet n'est pas fourni dans ce ZIP, afin de **préserver la version régénérée par Symfony sur MAIN** : le préflight impose que cet écart soit exactement le seul changement, puis l'indexation explicite le publie dans le même commit versionné que ce contrat et son test. Aucune conversion de fins de ligne n'est requise.

Messenger reste sans transport ni routage, et aucun handler / consommateur n'est activé. Aucun accès à `data/queue/global.sqlite`, aucun job, aucun changement aux processus ROOT/FastCGI/watchdog/PROD.

Si l'écart attendu n'est plus présent ou comporte d'autres lignes, interrompre l'application, sans régénérer artificiellement ni restaurer le fichier. Le prochain lot, distinct, traite l'exclusivité GPU et le fencing de la queue canonique.
