from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .core.config import get_settings
from .api.endpoints import kanban
from .models.base import Base
from .database import engine

# Create database tables
Base.metadata.create_all(bind=engine)

settings = get_settings()
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="API para la gestión de un tablero Kanban",
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://my-planning-crisaraozs-projects.vercel.app",
        "https://my-planning-tawny.vercel.app",
        "http://localhost:3000",
    ],  # Dominios específicos permitidos
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Include routers
app.include_router(
    kanban.router,
    prefix=settings.API_V1_STR,
    tags=["kanban"]
) 