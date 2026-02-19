"""
Point d'entrée de l'application FastAPI.

Configure et lance l'API REST pour le pipeline Anki.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.adapters.primary.fastapi.routers import analyst_router
from src.adapters.primary.fastapi.routers.restructurer_router import router as restructurer_router
from src.adapters.primary.fastapi.routers.generator_router import router as generator_router
from src.infrastructure.logging.config import setup_logging, get_logger


# Configuration du logging structuré
setup_logging(log_dir="logs", json_format=False)
logger = get_logger(__name__, "main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestion du cycle de vie de l'application."""
    # Startup
    logger.info("Démarrage de l'application Anki Doc Master")
    yield
    # Shutdown
    logger.info("Arrêt de l'application")


# Création de l'application
app = FastAPI(
    title="Anki Doc Master API",
    description="""
API pour le pipeline de génération de cartes Anki.

## Pipeline

Le pipeline est composé de plusieurs étapes :

1. **Analyste** : Évalue le contenu d'un document selon les modules disponibles
2. **Restructureur** : Restructure le document selon les modules recommandés
3. **Générateur** : Crée les cartes Anki (basic ou cloze) à partir du contenu restructuré
4. **SuperMemo Expert** : Applique les règles SuperMemo
5. **Anki Syntax Expert** : Produit les fichiers Anki

## Modules disponibles

- **themes** : Sujets principaux et sous-thèmes
- **vocabulary** : Termes techniques et définitions
- **images** : Schémas, diagrammes, photos
- **tables** : Tableaux de données
- **math_formulas** : Équations et formules
- **code** : Blocs de code et exemples
    """,
    version="0.1.0",
    lifespan=lifespan
)

# Configuration CORS pour le frontend PySide6
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En production, restreindre aux origines autorisées
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Enregistrement des routers
app.include_router(analyst_router)
app.include_router(restructurer_router)
app.include_router(generator_router)


@app.get("/", tags=["Health"])
def root():
    """Endpoint de santé."""
    return {
        "status": "ok",
        "service": "Anki Doc Master API",
        "version": "0.1.0"
    }


@app.get("/health", tags=["Health"])
def health_check():
    """Vérification de l'état de l'API."""
    return {
        "status": "healthy",
        "checks": {
            "api": "ok"
        }
    }
