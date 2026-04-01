"""
MIRA Stylist — Backend Application
A premium AI stylist experience.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from .utils.env import get_settings
from .routes import health, onboarding, profile, tryon, saved_looks, sizing, stylist, motion, voice

settings = get_settings()

app = FastAPI(
    title="MIRA Stylist",
    description="Premium AI Fashion Stylist — Personalized styling, virtual try-on, and editorial intelligence.",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler — never expose raw errors
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "Something unexpected happened on our end. Please try again.",
            "data": None,
            "errors": None,
        },
    )


# Register routers
app.include_router(health.router)
app.include_router(onboarding.router)
app.include_router(profile.router)
app.include_router(tryon.router)
app.include_router(saved_looks.router)
app.include_router(sizing.router)
app.include_router(stylist.router)
app.include_router(motion.router)
app.include_router(voice.router)
app.mount("/media", StaticFiles(directory=settings.DATA_DIR), name="media")


@app.get("/")
async def root():
    return {
        "service": "MIRA Stylist",
        "version": "1.0.0",
        "message": "Welcome to MIRA — your personal AI stylist.",
    }
