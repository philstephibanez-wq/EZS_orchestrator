# 4.2c13 — Supervision Assistant

Sondes GET sur la façade 8712 : /api/health puis /api/inference/status. L'interface affiche séparément la disponibilité de l'Assistant Web et du moteur IA. Aucun POST /api/profile/verify : cette route exécute réellement une expertise.

Aucun claim, job #193, dispatch ou retour LAB déclenché. Aucun changement START/STOP, LAB, Assistant, PROD. Test synthétique ajouté, validation MAIN en attente. La disponibilité ne prouve pas l'idempotence ou le trajet LAB → Assistant → LAB.
