# v2.b1 — correctif contrat DEV idempotent

Recette MAIN de v2.b0 : `powershell -ExecutionPolicy Bypass -File .\scripts\start.ps1` → `EZS_DEV_ALREADY_RUNNING_VERIFIED`. `v2_lifecycle.ps1 -Action status` → `php_owned=True caddy_owned=True state_present=True`. **Le runtime DEV est sain.** Le contrat `DevStartIdempotency2B0ContractTest.php` échouait à tort sur `18515` présent exclusivement dans un commentaire de séparation PROD de `start.ps1`.

v2.b1 ignore les commentaires PowerShell de pleine ligne dans son assertion de non-régression et continue de refuser les appels exécutables de gateway (état gateway, port 18515, `-Target gateway`). Aucun script lifecycle, port ni processus modifié.

Validation à exécuter sur MAIN : `php tests/DevStartIdempotency2B0ContractTest.php` ; la vérification runtime a déjà été exécutée avec succès par le mainteneur avant ce correctif. La suppression des scripts historiques supplémentaires et la migration PHP globale restent ouvertes.
