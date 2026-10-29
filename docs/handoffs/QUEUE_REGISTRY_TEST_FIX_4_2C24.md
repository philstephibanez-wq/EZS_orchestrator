# Handoff v4.2c24 — Test de snapshot conservé entre versions

Recette Windows du mainteneur sur v4.2c23 : lint GlobalQueueStore OK ; GlobalQueueStore42C23 OK ; JobRegistry42C3 OK. QueueRegistrySnapshot42C22 échoue uniquement sur la garde exacte VERSION=4.2c22 (la version active est 4.2c23), avant ses assertions SQLite. Correction minimale du test : accepter les versions 4.2c22 et suivantes de cette série, sans modifier le code runtime. Nouveau passage du test requis, aucune validation SQLite snapshot revendiquée avant son retour. Aucun job réel ni script START/STOP modifié.
