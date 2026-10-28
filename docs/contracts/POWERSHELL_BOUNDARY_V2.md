# Contrat de migration V2 — frontière PHP/PowerShell et sûreté PROD (v2.a49)

## Décision canonique du mainteneur

L'Orchestrator doit être exécuté en **PHP 8.5 / Symfony**, sans composant Python interne **après validation effective de la bascule**. **Exception à la purge : préserver des points d'entrée opérationnels START, STOP, STATUS et REPAIR** jusqu'à remplacement fonctionnel éprouvé. Les opérations qui agissent sur des processus doivent refuser un PID non attesté ; aucune fenêtre console Windows 11 n'est acceptable. La maintenance PROD ne doit pas être interrompue pendant la migration.

## État vérifié dans GitHub master v2.a48

- `scripts/start.ps1`, `scripts/stop.ps1`, `scripts/v2_lifecycle.ps1` ont été restaurés dans v2.a48. Leurs actions DEV sont historiquement `start/stop/status/repair`.
- `scripts/prod_lifecycle.ps1` appelle encore `H:\Python\pythoncore-3.14-64\python.exe` pour `runtime_components/prod_gateway/server.py` sur 8510 et gère `start/stop/status/maintenance/normal/repair-fastcgi`.
- Un candidat PHP-FastCGI existe (`runtime_components/prod_gateway_php/router.php`, Caddy 18514, php-cgi 18515). La recette isolée v2.a41e a réussi, mais **SSO/médias réels, responsabilité permanente du processus et rollback réel ne sont pas validés**.
- Le service Symfony `DevLifecycle` est seulement en lecture seule et refuse toutes les actions mutantes. Le comparer à un remplaçant opérationnel serait faux.

## Gate obligatoire, non contournable

1. Implémentation effective et supervision sûre du gateway PHP-FastCGI avec identité Windows (PID, chemin absolu, commande, création, ownership du listener), sans wrapper PowerShell/Python et sans flash de fenêtre.
2. Test sur MAIN du candidat isolé pour SSO Google, sessions et cookies, `/internal/media/auth`, flux volumineux/concurrents et comportement de maintenance.
3. Implémentation Symfony opérationnelle du lifecycle DEV et PROD, avec verrou, préflight, start/stop/repair/status, rollback, protections de ports, refus des états stales et authentification des opérations.
4. Validation MAIN d'une recette sûre en maintenance, rollback exercé et continuité vérifiée avant toute prise de 8510.
5. **Seulement alors** suppression dans le même lot des deux derniers composants Python/PowerShell PROD, après vérification des références. Le mainteneur a demandé que les commandes start/stop/repair restent accessibles, même si leur implémentation interne change.

## Discipline de preuve

Les contrats PHP statiques ne prouvent ni une mise en service native ni le zéro console. Les livraisons ne doivent pas déclarer la purge complète si le gateway Python reste nécessaire à la restauration. Ne jamais arrêter PROD au titre d'un simple nettoyage Git. Le présent correctif réconcilie les tests contradictoires sans déclencher d'action réelle.
