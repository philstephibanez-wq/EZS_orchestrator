# EZS_orchestrator R3.20 — UTF-8 CLI

Le service et l'executor capturent déjà les subprocess en UTF-8. R3.20 rend
aussi `control_center.cli` explicitement UTF-8 sous Windows afin qu'une sortie
worker contenant des caractères Unicode ne puisse pas provoquer un
`UnicodeEncodeError`.

Aucun changement du scheduler, des targets, du singleton GPU ni du lifecycle
DEV/PROD.
