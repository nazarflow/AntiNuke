# src/api/app.py
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from src.api.routers import admins, guilds, limits

app = FastAPI(
    title="AntiNuke Dashboard API",
    description="REST API for managing AntiNuke bot configuration and limits.",
    version="1.0.0",
)

# Configure CORS so the frontend (running on e.g., localhost:5173 during dev) can communicate with the API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify the actual frontend domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include separated domain routers
app.include_router(admins.router)
app.include_router(guilds.router)
app.include_router(limits.router)

@app.get("/api/health", tags=["System"])
async def health_check():
    return {"status": "ok", "service": "AntiNuke API"}

# Mount frontend directory at root URL to serve index.html
if os.path.exists("frontend"):
    app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
