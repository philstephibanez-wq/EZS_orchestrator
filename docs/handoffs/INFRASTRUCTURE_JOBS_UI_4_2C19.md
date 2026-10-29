# Handoff 4.2c19 — Harmonisation du dashboard

Relecture des deux templates, deux contrôleurs et sondes `LabQueueProbe` et `AssistantReadinessProbe` : sondes existantes GET uniquement. Migration des statuts LAB/IA vers Infrastructure ; suppression du panneau IA de Files & Jobs ; conservation du tableau LAB et des archives. Grille uniforme des détails DEV/PROD/LAB/Assistant. Aucun comportement de lifecycle ou jobs modifié. État des sondes rendu à l'ouverture de la page : actualisation par rechargement, alors que HTTP/TCP reste actualisé par JS. Recette Windows et visuelle non effectuée.
