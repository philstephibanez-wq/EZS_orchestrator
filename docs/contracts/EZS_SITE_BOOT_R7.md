# EZS Orchestrator - R7 - démarrage unique des sites et ping hard

Décision opérateur du 3 novembre 2026. Cette disposition locale supplante, pour le lancement des sites uniquement, les prescriptions historiques d'intention persistée dans le contrat général. Le mode Normal/Maintenance PROD, l'identité des propriétaires, les incidents et les journaux restent persistants.

- Au lancement du résident ROOT, après succès HTTP de ROOT, exécuter une seule tentative de boot DEV, LAB, Assistant, PROD, dans cet ordre.
- Si mode Maintenance, Transition ou Failed, ne jamais démarrer PROD.
- Si un site est attesté opérationnel, le laisser intact. Si totalement absent, vérifier et lancer via son adaptateur canonique. Si état partiel ou étranger, ne pas lancer en doublon, ne tuer aucun PID et journaliser l'échec.
- Le lancement produit un ping hard (inventaire processus, ports) après chaque démarrage. Le status suivant est non destructif. L'échec d'un site ne bloque pas la collecte des autres.
- Le polling ultérieur ne redémarre jamais les sites. Au redémarrage du résident ROOT seulement, la nouvelle session exécute un nouveau boot initial.
- Les commandes manuelles seront homogénéisées sans persistance dans une livraison distincte ; l'ancien contrôleur HTTP reste pour l'instant un écart à ce contrat.
- Le ping soft, la bascule automatique et le retour manuel en mode Normal sont des étapes distinctes, non activées ici.
- PROD reste protégé contre l'arrêt via le lanceur général. La bascule Maintenance est exclusivement gouvernée par le mécanisme dédié R6B.

Limite de sécurité : un site existant dont l'identité ou les ports sont incohérents reste UNVERIFIED et ne doit ni être adopté ni être démarré en doublon. R7 ne garantit pas que tous les services soient RUNNING si MAIN présente cet état.
