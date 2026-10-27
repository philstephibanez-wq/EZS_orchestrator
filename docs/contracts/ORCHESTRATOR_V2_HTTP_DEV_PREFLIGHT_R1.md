# V1.3b10 — Préflight HTTP Symfony isolé (sans bascule)

## Objet
Tester le chemin **Caddy → PHP-CGI FastCGI → Symfony 7.4** sur MAIN avant toute intégration au Caddy DEV commun.

La configuration candidate est `web/config/caddy/Caddyfile.dev-preflight` :
- HTTP **127.0.0.1:8790 uniquement** ;
- FastCGI **127.0.0.1:8791** ;
- interface d'administration Caddy **désactivée dans ce candidat de test** ;
- racine Symfony `H:/EZS_orchestrator/web/public` ;
- fichier de configuration volontairement distinct de PROD et de Caddy DEV canonique.

## Interdictions
Ne pas lancer un deuxième Caddy si un Caddy DEV existe déjà. Ne pas traiter ce candidat comme le Caddy DEV définitif. Ne pas modifier/occuper EZScore PROD 8501, EZScore DEV 8502, LAB 8701, ni leurs routes, SSO, Cloudflare, médias et certificats. Ne pas tuer le processus LAB historique. Pas de `php -S`, ni tâche planifiée, ni launcher persistant ajouté.

## Validation MAIN sans démarrer de service
```powershell
cd H:\EZS_orchestrator
php .\web\tests\CaddyPreflightContractTest.php
& 'H:\Caddy\caddy.exe' validate --config 'H:\EZS_orchestrator\web\config\caddy\Caddyfile.dev-preflight' --adapter caddyfile
Get-NetTCPConnection -State Listen | Where-Object { $_.LocalPort -in @(8501,8502,8701,8790,8791,2019) }
```

## Test HTTP encadré — seulement après validation et contrôle d'absence de Caddy DEV actif
1. Préparer `APP_ENV=dev`, `APP_DEBUG=1` et `APP_SECRET` dans l'environnement du backend PHP-CGI ; ne jamais committer de secret.
2. Démarrer **temporairement** le backend `H:\PHP\php-8.5-x64\php-cgi.exe -b 127.0.0.1:8791` (mode FastCGI, sans `php -S`).
3. Démarrer Caddy avec la configuration candidate sur 8790 uniquement si aucune instance Caddy DEV n'est active. Ce lancement est un essai jetable, pas un nouveau mécanisme canonique.
4. Tester `http://127.0.0.1:8790/api/v2/environments` puis `http://127.0.0.1:8790/` et le chargement des assets. Vérifier les codes 200 et contenu, pas seulement l'ouverture du port.
5. Arrêter uniquement les PID exacts lancés pour cet essai, jamais des services préexistants ; contrôler que 8501/8502 et 8701 sont restés inchangés.

## Limites
Le fichier est une **configuration de préflight**, pas un déploiement. Le routage PROD/DEV commun reste à concevoir, les instances doivent conserver leurs singletons par rôle. Les fichiers CDN de l'interface demandent encore une distribution locale avant production. Si FastCGI échoue, diagnostiquer le runtime PHP avant tout changement aux ports canoniques. Aucun service n'a été lancé au moment de cette livraison.
