# 1.3b9 — Sondes DEV en lecture seule
- Nouveau GET /api/v2/infrastructure/listeners ; contrôle TCP loopback borné à 250 ms sur les ports DEV connus 8502, 8702, 8712.
- Ceci mesure uniquement la présence d'un listener TCP, **pas** la santé applicative, la propriété du processus, l'authentification ou l'état du worker.
- Port PROD 8501 non sondé, aucun accès au processus Caddy PROD, aucun service démarré.
- Aucune action REST mutante, aucun changement de configuration Caddy. Tester sous Symfony en HTTP avant de publier les données de statut comme état métier.
- Test : php web/tests/LocalPortStatusTest.php ; puis lint:container et debug:router.
- Suite bloquante : HTTP derrière Caddy DEV sans changer 8502/8501 ; vérification auth et cycle de vie canonique avant suppression de web.py.
