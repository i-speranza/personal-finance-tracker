"""FastAPI application main file."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from .database import engine, Base
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


@app.get("/")
async def root():
    """Root endpoint - serve index.html."""
    if is_production:
        index_path = os.path.join(frontend_dist_path, "index.html")
    else:
        index_path = os.path.join(frontend_path, "index.html")
    
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Personal Finance Tracker API", "version": "1.0.0"}


@app.get("/upload.html")
async def upload_page():
    """Serve upload.html."""
    if is_production:
        upload_path = os.path.join(frontend_dist_path, "upload.html")
    else:
        upload_path = os.path.join(frontend_path, "upload.html")
    
    if os.path.exists(upload_path):
        return FileResponse(upload_path)
    return {"error": "Upload page not found"}


@app.get("/edit.html")
async def edit_page():
    """Serve edit.html."""
    if is_production:
        edit_path = os.path.join(frontend_dist_path, "edit.html")
    else:
        edit_path = os.path.join(frontend_path, "edit.html")
    
    if os.path.exists(edit_path):
        return FileResponse(edit_path)
    return {"error": "Edit page not found"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


# Import routers (will be added in future implementation)
# from .routers import transactions, investments, assets, dashboard, export
# app.include_router(transactions.router, prefix="/api/transactions", tags=["transactions"])
# app.include_router(investments.router, prefix="/api/investment-products", tags=["investments"])
# app.include_router(assets.router, prefix="/api/assets-history", tags=["assets"])
# app.include_router(dashboard.router, prefix="/api/dashboard", tags=["dashboard"])
# app.include_router(export.router, prefix="/api/export", tags=["export"])
