# v2.a13 — arrêt singleton et façades Caddy DEV

Sur MAIN, le démarrage v2.a12 fonctionne et le second démarrage est refusé. Le stop échoue sur 8502, façade du Caddy DEV détenu par l'Orchestrator. Ce refus est incorrect. Le correctif autorise 8502 et 8852 uniquement lorsque leur PID est celui du Caddy enregistré et déjà validé ; les backends 8602, 8701, 8702, 8712 et 8862 restent bloquants tant que leur ownership n'est pas implémenté. Aucun port PROD n'est ciblé.

Revue statique GitHub uniquement. Sur MAIN, exécuter le lint PowerShell, le test PHP puis stop/status et confirmer les ports et les PID. Le retrait de web/ et le superviseur DEV complet ne font pas partie du correctif.
