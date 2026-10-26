# Bouton Ouvrir Assistant — Orchestrator 1.3a(17)

Dans Infrastructure > Assistant Docker MAIN : lien **Ouvrir Assistant** ouvrant `http://127.0.0.1:18713/` dans un nouvel onglet (`noopener noreferrer`). Aucun démarrage ni changement d'état implicite. Les contrôles Start/Stop du Web demeurent distincts. Les notifications de contrôle font référence à MAIN, plus à XPS.

Recette : `python -m py_compile control_center/web.py`, redémarrage ciblé du Control Center, Ctrl+F5, clic sur le lien. L'image Docker Web existante affiche encore v1.6a(127) : sa reconstruction relève d'une autre livraison avec validation Symfony, ce bouton ne la corrige pas. La chaîne LAB->Orchestrator->Assistant->LAB n'est pas encore livrée.
