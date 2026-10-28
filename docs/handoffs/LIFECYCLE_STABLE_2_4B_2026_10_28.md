# EZS Orchestrator 2.4b — STABLE (cycle START/STOP)

Date : 28 octobre 2026. Décision explicite du mainteneur : **START et STOP global testés et OK sur MAIN ; clore ce chantier et déclarer la version 2.4b stable**.

## Portée réellement validée

- `scripts/stop.ps1` et `scripts/start.ps1` fonctionnent sur MAIN selon le retour opérateur.
- Les backends FastCGI EZScore DEV (8602 et 8862), LAB (8701), Assistant (8713) et Orchestrator (8791) sont couverts par le cycle global.
- Caddy DEV partagé reste autonome, ses façades restent configurées et ne sont pas arrêtées par STOP.
- La maintenance PROD est une opération explicite du STOP global et PROD n'est pas arrêtée ni déployée.
- Les propriétaires de processus sont contrôlés avant arrêt pour éviter de terminer un processus étranger.

## Limites explicites

**Stable désigne ici le cycle START/STOP testé**, pas l'achèvement de la migration Symfony/PHP de l'issue #18. L'intégration complète des workers IA, de Qwen, du guardian, des queues Symfony, du nettoyage legacy et des tests SSO/médias de bout en bout restent des sujets distincts. Aucune exécution de test local n'a été réalisée par l'assistant lors du commit de stabilisation : le retour utilisateur constitue la preuve opérateur START/STOP.

## Traçabilité

Dernier correctif fonctionnel : v2.b14, commit `9cf15c1e313e8130291f9fc4f273c2b379dade9d`.
Promotion stable demandée : `VERSION=2.4b` ; commit de clôture sans modification runtime. Test de garde : `php tests/LifecycleStable24BContractTest.php`.

## Clôture documentaire du 28 octobre 2026

Le mainteneur a confirmé une deuxième fois START/STOP OK et demandé de **figer 2.4b sans nouvelle révision**. À sa demande, les issues, contrats et handoffs sont alignés à cette référence. Ce complément documentaire ne constitue ni un changement runtime ni une nouvelle version. La migration globale Symfony/PHP de l'issue #18 reste ouverte ; son volet START/STOP est clos.
