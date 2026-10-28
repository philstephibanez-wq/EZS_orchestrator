# v2.b12 — correction de la supervision LAB

MAIN a montré LAB 8702 GET / HTTP 302 puis /home HTTP 200, mais la carte Orchestrator affiche parfois TCP seul. La source reconnaissait déjà les redirections 302 : délai de lecture HTTP trop court (700 ms) et tentative de lire HTTP sur le backend FastCGI 8701, qui n'est pas un serveur HTTP.

Correction limitée à Orchestrator : 1500 ms de lecture de statut HTTP, port FastCGI LAB mesuré en TCP seulement, timeout AJAX 9 s et libellé backend correspondant. Aucune modification LAB, Assistant, Caddy, PROD ni science. Ne pas redémarrer Caddy.

Recette MAIN : pull, `php tests/LabHttpProbe2B12ContractTest.php`, rafraîchir 8790, vérifier HTTP 302/200 et badge LAB « Répond », backend « FastCGI TCP ouvert ». Validation MAIN non encore effectuée.
