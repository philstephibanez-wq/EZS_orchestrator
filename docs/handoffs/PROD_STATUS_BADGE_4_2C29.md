# 4.2c29 — Badge de statut PROD et test REST

Le libellé PROD `Gateway et Symfony actifs` était rendu avec la classe Bootstrap initiale `text-bg-secondary` sans mise à jour JS. Appliquer success quand gateway_online et backend_ready sont vrais ; warning quand seule la gateway répond ; danger gateway absente ; secondary quand la supervision échoue. Supprimer les anciennes classes avant affectation. Aucun changement de la logique serveur de maintenance ni du backend.

Correction d'un ancien test 4.2c27 qui imposait une égalité VERSION malgré les nouvelles versions. Aucun changement du comportement REST.

Recette : test PHP de contrat, ancien test REST, syntaxe JS si Node disponible, rechargement navigateur forcé, contrôler que l'API renvoie gateway_online=true et backend_ready=true avant de conclure au badge vert. Aucun script START/STOP ou job modifié.
