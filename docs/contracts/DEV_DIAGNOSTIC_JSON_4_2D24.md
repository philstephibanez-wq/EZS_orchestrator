# Diagnostic DEV — JSON brut, console vert/noir

Périmètre : Twig layout de ROOT, diagnostic du navigateur et GET de supervision DEV/LAB/Assistant.
Aucun START/STOP, aucune opération PROD.

- Chaque collecte est identifiée par source, méthode, chemin, timestamp UTC, code HTTP et durée.
- Corps JSON renvoyé par la source conservé tel quel pour les champs non sensibles ; les secrets et identifiants privés sont masqués explicitement.
- L'API `dev-groups` peut fournir un CSRF : le dump doit **obligatoirement** le masquer.
- Les réponses non JSON et les corps au-delà de 120000 caractères sont déclarés explicitement, jamais exposés comme données brutes non filtrées.
- Le DOM est présenté comme une source indépendante sans calcul de conformité.
- Aucun état synthétique ONLINE/OFFLINE/ERREUR ne doit apparaître dans la console.
- « Copier » reproduit strictement le texte de la console.
- Limite : requêtes POST réelles non interceptées. Les traces de START/STOP restent celles des endpoints GET autorisés. Pas de preuve opérationnelle de l'arrêt natif.
