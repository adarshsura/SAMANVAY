import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.database.session import engine, Base, SessionLocal
from app.database.seed_data import seed_all_data

# Routers
from app.api.auth import router as auth_router
from app.api.citizen import router as citizen_router
from app.api.incidents import router as incidents_router
from app.api.resources import router as resources_router
from app.api.optimization import router as optimization_router
from app.api.responder import router as responder_router
from app.api.simulation import router as simulation_router
from app.api.dashboard import router as dashboard_router
from app.api.audit import router as audit_router
from app.api.websocket import router as ws_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SAMANVAY-AI")

_db_initialized = False

def init_db():
    global _db_initialized
    if not _db_initialized:
        logger.info("Initializing database schema...")
        Base.metadata.create_all(bind=engine)
        db = SessionLocal()
        try:
            seed_all_data(db)
            _db_initialized = True
        except Exception as e:
            logger.error(f"Error during database initialization: {e}")
        finally:
            db.close()
        logger.info("SAMANVAY AI Engine Ready.")

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="AI-Powered Disaster Resource Allocation & Coordination Platform",
    lifespan=lifespan
)

@app.middleware("http")
async def ensure_db_ready_middleware(request, call_next):
    if not _db_initialized:
        init_db()
    return await call_next(request)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(citizen_router, prefix=settings.API_V1_STR)
app.include_router(incidents_router, prefix=settings.API_V1_STR)
app.include_router(resources_router, prefix=settings.API_V1_STR)
app.include_router(optimization_router, prefix=settings.API_V1_STR)
app.include_router(responder_router, prefix=settings.API_V1_STR)
app.include_router(simulation_router, prefix=settings.API_V1_STR)
app.include_router(dashboard_router, prefix=settings.API_V1_STR)
app.include_router(audit_router, prefix=settings.API_V1_STR)
app.include_router(ws_router) # /ws

@app.get("/api/health")
def health_check():
    return {
        "status": "HEALTHY",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "solver": "OR-Tools SCIP MILP"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
