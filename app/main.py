from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.endpoints.transcription import router as transcription_router
from .api.endpoints.summary import router as summary_router
from .api.endpoints.docs import router as docs_router

app = FastAPI(
    title="AI Dev Tools API",
    description="API para transcripción y resumen de videos de YouTube, y procesamiento de documentación",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost",
        "https://localhost:3000",
        "https://localhost:3001",
        "https://localhost",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "*",  # Allow all origins for testing - remove in production
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include transcription router
app.include_router(
    transcription_router,
    prefix="/api/v1/transcription",
    tags=["transcription"]
)

# Include summary router
app.include_router(
    summary_router,
    prefix="/api/v1/summary",
    tags=["summary"]
)

# Include docs router
app.include_router(
    docs_router,
    prefix="/api/v1/docs",
    tags=["documentation"]
) 