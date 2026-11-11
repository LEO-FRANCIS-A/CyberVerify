import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.core.config import settings
from backend.app.database.mongo import connect_to_mongo, close_mongo_connection
from backend.app.api.routes import router as api_router
from backend.app.services.source_registry_service import seed_source_registry

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("cyberverify")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize DB and Source Registry
    logger.info("Initializing CyberVerify application services...")
    await connect_to_mongo()
    try:
        await seed_source_registry()
    except Exception as e:
        logger.warning(f"Could not seed source registry on startup: {e}")
    yield
    # Shutdown: Close DB
    logger.info("Shutting down CyberVerify application services...")
    await close_mongo_connection()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="CyberVerify Dual-Engine Platform: Claim Verification & Real-Time Event Intelligence",
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API router
app.include_router(api_router, prefix=settings.API_PREFIX)

@app.get("/")
async def root():
    return {
        "service": "CyberVerify Dual-Engine API",
        "version": settings.VERSION,
        "docs_url": "/docs",
        "api_prefix": settings.API_PREFIX
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
