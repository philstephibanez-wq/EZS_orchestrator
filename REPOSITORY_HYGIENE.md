# ⛔ HYGIÈNE DU DÉPÔT — RÈGLE OBLIGATOIRE

## INTERDICTION ABSOLUE DE POLLUER LE DÉPÔT

Le dépôt doit contenir uniquement des fichiers **durables et nécessaires au produit**.

Tous les éléments temporaires ou liés à une intervention ponctuelle doivent être créés **hors du dépôt**, sous :

```text
H:\temp
```

Cette règle s'applique notamment à :

- tests ponctuels, tests de contrat temporaires et scripts de vérification ad hoc ;
- scripts d'installation ou de provisioning ponctuels ;
- scripts `apply-*`, `migrate-*`, `preflight-*`, `hotfix-*`, `rollback-*` temporaires ;
- sauvegardes `*.bak`, `*.before_*`, copies avant migration et snapshots ;
- ZIP de livraison, fichiers d'extraction et README de livraison intermédiaires ;
- logs, traces, dumps, exports de diagnostic, caches et artefacts générés ;
- bases de données locales, fichiers audio/imports, modèles téléchargés et résultats d'analyse ;
- tout autre fichier créé uniquement pour développer, tester, migrer, diagnostiquer ou livrer une modification.

## H:\temp EST JETABLE

`H:\temp` peut être purgé régulièrement et **sans préavis**.

En conséquence :

1. le produit ne doit jamais dépendre d'un fichier temporaire présent dans `H:\temp` ;
2. un fichier nécessaire au fonctionnement permanent doit être conçu comme un vrai composant du produit, nommé sans numéro de patch/hotfix et versionné intentionnellement ;
3. aucun fichier temporaire ne doit être ajouté à Git « pour garder une trace » ;
4. avant tout `git add` ou commit, vérifier explicitement `git status --short` et exclure toute pollution ;
5. ne jamais utiliser `git add .` ou `git add -A` dans un dépôt contenant des fichiers non vérifiés.

## RÈGLE POUR LES ASSISTANTS ET AUTOMATISATIONS

Tout assistant, agent, script ou automatisation intervenant sur ce dépôt doit respecter cette règle par défaut.

**Si un fichier n'est pas clairement un composant durable du produit, il doit être créé dans `H:\temp`, pas dans le dépôt.**

## VERSIONING DES LIVRAISONS

Le fichier `VERSION` fait partie des composants durables du produit et doit être versionné intentionnellement.

- Toute livraison poussée doit incrémenter `VERSION`.
- `release` : `MAJOR.MINOR.PATCH`.
- `fix` : suffixe lettre minuscule sur la release courante (`1.5.0a`, `1.5.0b`, ...).
- Le SHA Git est une révision technique séparée et ne remplace jamais la version humaine.
- Un commit destiné au push qui ne met pas à jour `VERSION` est non conforme.

