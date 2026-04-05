"""FastAPI application - Main entry point for web API"""

import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import auth
from app.websocket import terminal
from app.routers import forms, commands
from app.routers.transfer import router as transfer_router
from app.core.database import init_database, close_database

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

# Reduce noise from libraries
logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown"""
    # Startup
    try:
        init_database()
    except Exception as e:
        raise
    
    yield
    
    # Shutdown
    close_database()

# Create FastAPI app
app = FastAPI(
    title="MongoDB Manager API",
    description="Web API for MongoDB backup and restore management",
    version="2.0.0",
    lifespan=lifespan
)

# Get CORS origins from environment variable
cors_origins_env = os.getenv("CORS_ORIGINS", "http://localhost:3000")
cors_origins = [origin.strip() for origin in cors_origins_env.split(",")]

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(forms.router, tags=["forms"])  # HTTP forms API
app.include_router(commands.router, tags=["commands"])  # HTTP commands API
app.include_router(terminal.router, tags=["terminal"])  # WebSocket terminal
app.include_router(transfer_router, tags=["transfer"])  # Export / Import

# Health check endpoint
@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "service": "mongodb-manager-api"
    }

# Root endpoint
@app.get("/")
def root():
    """Root endpoint"""
    return {
        "message": "MongoDB Manager API",
        "version": "2.0.0",
        "docs": "/docs",
        "health": "/health"
    }
