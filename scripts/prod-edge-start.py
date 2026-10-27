"""Entrée indépendante du répertoire courant pour la façade PROD."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from prod_lifecycle.edge_bootstrap import main

if __name__ == "__main__":
    raise SystemExit(main())
