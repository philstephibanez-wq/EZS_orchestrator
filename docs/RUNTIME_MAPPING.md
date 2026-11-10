# Mapping canonique des entrees, sorties et endpoints EZS

**Contrat** : `ezs.runtime.endpoints.v1` — [issue #27](https://github.com/philstephibanez-wq/EZS_orchestrator/issues/27).

## Sources de verite

- `config/runtime.json` (schema `ezs.orchestrator.config.v5`) : adresses et racines configurees.
- `config/frankenphp/Caddyfile.{dev,prod,lab}.native` : chaines de proxy et routes internes de FrankenPHP.
- `docs/endpoints.v1.json` : inventaire versionne des endpoints dont la declaration ou l'observation est confirmee.
- `php bin/console debug:router` de **chaque application** : source de verite des routes Symfony reelles ; cet inventaire doit etre actualise au changement de route.
- `runtime/**` : etat ephemere, **non versionne** ; un PID enregistre n'atteste pas de la vie du processus.

Ne jamais utiliser un balayage de ports pour deviner la topologie. Lire d'abord le contrat, puis effectuer une verification reseau facultative. Les tests HTTP ne remplacent pas la configuration et une reponse HTTP ne constitue pas une preuve de bon fonctionnement metier.

## Topologie declaree

| Service | Racine | Entree publique | Sortie interne |
|---|---|---|---|
| EZScore DEV | `H:\EZScore_dev` | `127.0.0.1:8502` | backend Symfony `127.0.0.1:8602` |
| EZScore PROD | `H:\EZScore` | `127.0.0.1:8501` | gateway `127.0.0.1:8510` vers backend Symfony `127.0.0.1:8511` |
| EZStudio LAB | `H:\EZStudio_lab` | `127.0.0.1:8702` | backend Symfony `127.0.0.1:8701` |
| Orchestrator | `H:\EZS_orchestrator` | `127.0.0.1:8700` documente dans README | controle interne a inventorier |

Les ports et adresses de DEV, PROD et LAB sont lus dynamiquement dans `runtime.json` par `scripts/runtime_endpoint_map.py`. L'Assistant dispose de son propre contrat applicatif ; aucune adresse distante ne doit etre supposee.

## Chaines ingress → egress

### DEV

`Client → Caddy/FrankenPHP :8502 → Symfony :8602`.

- Requetes ordinaires : reverse proxy vers `:8602`.
- `/media/*` : `forward_auth` vers `:8602/internal/media/auth`, puis `file_server` vers `{$EZSCORE_MEDIA_ROOT}`. Ce chemin est fourni par l'environnement ; ne jamais le deviner.

### PROD

`Cloudflare → Caddy/FrankenPHP :8501 → Gateway PHP :8510 → Symfony :8511`.

- Requetes ordinaires : reverse proxy vers `:8510` avec les entetes `X-Forwarded-*`.
- Le gateway a pour entree `runtime_components/prod_gateway_php/router.php` via rewrite interne ; les appels exacts du routeur vers Symfony restent a documenter dans leur propre contrat.
- `/media/*` : `forward_auth` vers `:8510/internal/media/auth`, puis service de fichiers `H:/EZScore/var/storage/stems` apres `strip_prefix /media`.
- `/__ezscore_gateway_status` est documente comme endpoint de statut du gateway ; sa disponibilite se teste sur **8510**, pas sur 8501.
- Un HTTP 503 public peut etre un mode maintenance legitime : ne pas confondre disponibilite et panne sans verifier son etat.

### LAB

`Navigateur → FrankenPHP :8702 → backend Symfony :8701 → routes LAB`.

Le chemin `/home` (route Symfony `workbench_home`, page Catalogue) et le diagnostic FIFO ont repondu en HTTP 200 le 10 novembre 2026. Le chemin `/catalogue` n'est pas la route de cette page.

### Assistant

Les routes Symfony de l'Assistant sont inventoriees par declaration. Son URL publique n'est pas determinee dans ce contrat ; elle doit etre etablie depuis sa configuration effective, sans sonde automatique ni hypothese de machine distante.

## Endpoints connus

Le manifeste `docs/endpoints.v1.json` distingue les routes declarees (`router_declared`) des reponses effectivement observees (`http_verified_2026-11-10`). Il recense :

- LAB : `GET /home`, `GET /internal/diagnostic/local-queue`, `POST /analysis/jobs/{id}/cancel`, `POST /catalogue/{id}/delete`, `POST /catalogue/{id}/phase/{phase}/delete`, `GET /catalogue/{id}/presets.zip`.
- Assistant : `GET /api/status`, `GET /backoffice`, `GET /api/inference/status`, `GET /api/profile/direct-research/{id}`, `GET /api/backoffice/inference`, `GET /api/backoffice/recordings`.
- PROD : gateway `GET /__ezscore_gateway_status` (documente).

Les chemins et methodes mutatifs ne doivent **jamais** etre appeles par le preflight. Les endpoints contenant un identifiant ou affichant des informations sensibles ne sont pas sondes automatiquement.

## Verification permanente

Depuis le depot Orchestrator (Python standard, sans dependance externe) :

```powershell
H:\Python\pythoncore-3.14-64\python.exe scripts\runtime_endpoint_map.py --check
H:\Python\pythoncore-3.14-64\python.exe -m unittest discover -s tests -p test_runtime_endpoint_map.py -v
```

`--check` effectue une validation **statique** et affiche la topologie sans reseau. Utiliser `--probe` uniquement lorsque des requetes GET de sante sont souhaitees ; le programme affiche seulement les codes et types de reponse, **jamais les corps JSON**. Les erreurs reseau n'alterent pas le contrat.

## Discipline de mise a jour

Lors d'une modification de port, proxy, route ou destination : mettre a jour le contrat et les tests dans **le meme correctif**, incrementer `VERSION`, verifier les `Caddyfile.*.native` et les routeurs Symfony. Le fichier `runtime.json` demeure la source de verite de l'environnement. Aucun token LAB, cle API, cookie, identifiant ou corps JSON diagnostique ne doit figurer dans Git.
