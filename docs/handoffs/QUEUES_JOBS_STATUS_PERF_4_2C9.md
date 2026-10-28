# 4.2c9 — États colorés et lecture bornée des archives

## Constats MAIN
La page 4.2c8 affiche 40 attempts LAB, avec succès/échecs non colorés. Le mainteneur signale un affichage lent. Tests 4.2c8 des contrôleurs, historique isolé et Twig réussis ; route HTTP /jobs visuellement opérationnelle. La lenteur n'est **pas encore chronométrée** sur MAIN.

## Correction
Le lecteur de traces V1 conserve les mêmes cibles DEV/PROD/LAB et la même structure `runtime/jobs/{target}/{job}/{run}/result.json`, mais n'ouvre plus le JSON de chaque tentative. Il sélectionne par métadonnées de fichier les `limit * 10` candidats récents (avec borne `limit <= 100`), puis ne décode que les candidats retenus jusqu'à `limit` résultats valides. Le parcours des répertoires demeure intégral ; la performance n'est donc pas garantie et doit être mesurée. Les snapshots très anciens ou invalides au-delà du buffer ne peuvent pas remplir complètement un résultat : limitation explicite.

Badges statut : completed vert, failed rouge, finalize_error orange, running bleu (archive), queued gris (archive). Les états historiques ne représentent pas la queue en direct. Les messages d'échec, error logs et payloads métier ne sont jamais exposés dans la vue.

## Recette et sécurité
Test PHP du lecteur avec 60 fichiers temporaires hors dépôt, tests historiques et lint Twig à exécuter sur MAIN. Contrôler /jobs, /api/jobs, les couleurs et le temps de réponse, sans toucher aux jobs réels ni consommer #181/#182/#185. Aucun changement du circuit LAB/Assistant, Messenger, START/STOP ou PROD.
