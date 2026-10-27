# Handoff v2.a6 — diagnostic GPU NVIDIA

Sur MAIN, `nvidia-smi.exe` a retourné : `NVIDIA GeForce RTX 2060, 0, 0, 6144, 55, 29.85, [N/A], 960, P0`. Le parseur CSV existant prend en charge neuf champs et convertit la limite de puissance `[N/A]` en null ; un test contractuel fixe ce cas réel.

Le processus Symfony appelait le nom `nvidia-smi` sans chemin absolu, alors que le binaire vérifié sur MAIN est `%WINDIR%/System32/nvidia-smi.exe`. v2.a6 essaie ce chemin explicitement sous Windows puis celui sous ProgramFiles/NVIDIA Corporation/NVSMI, garde la variable EZS_NVIDIA_SMI prioritaire et augmente le timeout à 10 s.

Le contrôleur DEV/loopback distingue une erreur de lancement et de configuration de la sonde sans publier stderr ni chemins locaux. HTTP 503 reste possible et honnête : aucun résultat GPU fictif. La recette MAIN doit confirmer la lecture réelle. Aucun script Python, CMD ou PS introduit ; aucune modification Caddy/PROD, et aucune certification zéro flash console.

## Correction v2.a7 — champs optionnels CSV
Le test MAIN `GpuMainCsvContractTest.php` a échoué : seuls les cinq champs obligatoires étaient normalisés ; les valeurs optionnelles conservaient les espaces préfixes (` 29.85`, ` [N/A]`, ` 960`, ` P0`). Normalisation `trim` des champs optionnels, sans modifier la gestion `[N/A]`→`null`. Test de contrat déjà présent, recette MAIN après pull obligatoire.
