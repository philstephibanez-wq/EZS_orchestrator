# v2.a36 — recette fonctionnelle isolée, sans modification PROD

Cette recette utilise trois serveurs locaux séparés : backend simulé sur **18511**, passerelle Python de référence sur **18510**, passerelle PHP candidate sur **18513**. Le fichier de configuration de recette est créé sous le TEMP de Windows. **Ne jamais lancer cette recette sur 8510, 8511, ni sur le serveur public.**

Étape A, dans le répertoire racine : `php bin/gateway_recipe.php init`.

Étape B, ouvrir trois terminaux et laisser chaque processus tourner, depuis la racine du dépôt :

**Terminal 1 :**
```powershell
php -S 127.0.0.1:18511 runtime_components/prod_gateway_php/recipe_backend.php
```
**Terminal 2 :**
```powershell
python runtime_components/prod_gateway/server.py --root "$env:TEMP\ezs-gateway-recipe-v2a36" --host 127.0.0.1 --port 18510
```
**Terminal 3 :**
```powershell
$env:EZS_GATEWAY_RECIPE_CONFIG = "$env:TEMP\ezs-gateway-recipe-v2a36\var\runtime\online-gateway.json"
php -S 127.0.0.1:18513 -t runtime_components/prod_gateway_php runtime_components/prod_gateway_php/router.php
```

**Terminal 4 :** `php bin/gateway_recipe.php compare`.

Le comparateur refuse de travailler tant que les deux instances de recette ne déclarent pas le port backend 18511. Il confronte GET, POST, redirection, cookies et chemin interne en mode normal et maintenance. **Attention : cette comparaison est une recette locale simulée, pas une homologation Google SSO/médias sur PROD**. La commande modifie uniquement son fichier de configuration TEMP.

Le port PROD 8510, la configuration `H:/EZScore/var/runtime/online-gateway.json`, Caddy et le `.py` en production restent intacts.
