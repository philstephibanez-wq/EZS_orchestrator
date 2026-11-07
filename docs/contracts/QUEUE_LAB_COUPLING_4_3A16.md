# Orchestrator 4.3a16 — raccordement de l’exécuteur LAB

Périmètre exclusif : la file canonique autorise une demande à la fois et le transport Messenger transmet la référence opaque à LAB. Les modèles, moteurs, résultats, catalogues et jobs historiques ne sont pas modifiés par le patch.

- Suppression de l’import automatique `lab:queue:admit-existing-profile --apply` lors du polling ; seules les demandes nouvellement créées et déjà présentes dans l’outbox LAB sont publiées.
- Frontière explicite et réversible `EZS_QUEUE_ACTIVE_FROM_ID` entre les admissions antérieures (conservées en SQLite) et les nouvelles admissions. Par défaut 1 ; aucun déplacement implicite de la frontière.
- La même frontière est appliquée au lecteur Messenger et au claim atomique. Les garanties d’un seul job `running` et de lease ne changent pas.
- Les bases SQLite de test ne reçoivent jamais la frontière de MAIN.
- Activation de la frontière séparée du patch ; ne jamais supprimer/annuler/rejouer les anciens jobs ni passer en force sur un processus `running`.
- La chaîne opérationnelle exige un consommateur Messenger existant explicitement en marche ; le patch n’installe pas de tâche, ne démarre pas de service et ne touche pas PROD.
- Recette : PHPUnit Orchestrator + LAB, Symfony/Twig, `git diff --check`, test unitaire sur base isolée, vérification HTTP, preuve d'un seul claim du job neuf, puis attestation de fin. Aucune preuve opérationnelle ne peut être déclarée avant cette recette.
- Rollback : restauration des sources et versions si aucune exécution nouvelle n’a été autorisée depuis l’application ; remettre la frontière à sa valeur précédente séparément.
