"""FastAPI application main file."""
import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from .database import engine, Base

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
# Import models to register them with Base.metadata
from . import models  # noqa: F401

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="Personal Finance Tracker API",
    description="API for managing personal finance transactions and investments",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for frontend
frontend_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend")
frontend_dist_path = os.path.join(frontend_path, "dist")

# Check if production build exists (dist folder)
is_production = os.path.exists(frontend_dist_path)

if is_production:
    # Production: Serve built files from dist
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist_path, "assets")), name="assets")
    # Serve other static files from dist root
    static_files = StaticFiles(directory=frontend_dist_path)
    app.mount("/static", static_files, name="static")
else:
    # Development: Serve from frontend/static for compatibility
    if os.path.exists(frontend_path):
        static_dir = os.path.join(frontend_path, "static")
        if os.path.exists(static_dir):
            app.mount("/static", StaticFiles(directory=static_dir), name="static")
        lib_dir = os.path.join(frontend_path, "lib")
        if os.path.exists(lib_dir):
            app.mount("/lib", StaticFiles(directory=lib_dir), name="lib")


def get_index_path():
    """Get the path to index.html based on environment."""
    if is_production:
        return os.path.join(frontend_dist_path, "index.html")
    return os.path.join(frontend_path, "index.html")


@app.get("/")
async def root():
    """Root endpoint - serve index.html."""
    index_path = get_index_path()
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Personal Finance Tracker API", "version": "1.0.0"}


@app.get("/upload")
async def upload_page():
    """Serve index.html for Vue Router /upload route."""
    index_path = get_index_path()
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"error": "Page not found"}


@app.get("/edit")
async def edit_page():
    """Serve index.html for Vue Router /edit route."""
    index_path = get_index_path()
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"error": "Page not found"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


# Import routers
from .routers import transactions, banks, accounts, assets_history, upload

app.include_router(transactions.router, prefix="/api/transactions", tags=["transactions"])
app.include_router(banks.router, prefix="/api/banks", tags=["banks"])
app.include_router(accounts.router, prefix="/api/accounts", tags=["accounts"])
app.include_router(assets_history.router, prefix="/api/assets-history", tags=["assets-history"])
app.include_router(upload.router, prefix="/api/upload", tags=["upload"])
