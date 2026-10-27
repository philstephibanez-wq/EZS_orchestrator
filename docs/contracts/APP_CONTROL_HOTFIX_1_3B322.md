# Hotfix v1.3b322

Après v1.3b321, la recette MAIN a révélé cinq erreurs de syntaxe PowerShell et une duplication du bas du script. Reconstruction intégrale à partir du script v1.3b32 connu syntaxiquement valide, puis remplacement exact de la garde Caddy par la vérification de sa sortie PowerShell, sans dépendre de LASTEXITCODE. Le test PHP ajoute des contraintes structurelles ; il **ne remplace pas** `Parser.ParseFile` sur MAIN. Pas de modification Caddy ni PROD. Ne pas exécuter start/stop/restart avant une recette complète (Parser 0 erreur, deux tests PHP, `status`).
