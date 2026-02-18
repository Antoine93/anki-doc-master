"""
Script de démarrage du serveur FastAPI.

Usage:
    python run.py
"""
import os
import sys
from pathlib import Path

# Ajouter le dossier backend au PYTHONPATH
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

# Charger les variables d'environnement
from dotenv import load_dotenv
load_dotenv()

import uvicorn


def main():
    """Lance le serveur FastAPI."""
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", 8000))

    print(f"Démarrage du serveur sur http://{host}:{port}")
    print(f"Documentation: http://{host}:{port}/docs")

    uvicorn.run(
        "src.main:app",
        host=host,
        port=port,
        reload=True
    )


if __name__ == "__main__":
    main()
