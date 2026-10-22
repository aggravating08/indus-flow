"""Indus Flow: Autonomous Supply Chain Resilience Agent Application Entrypoint."""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from src.api.routes import router as api_router
from src.config import settings

app = FastAPI(
    title="Indus Flow — Autonomous Supply Chain Resilience Agent",
    description="Enterprise Supply Chain Resilience Agent integrating Meterless World Model, Zetaris, and NVIDIA NIM.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Router
app.include_router(api_router, prefix="/api/v1", tags=["Supply Chain Intelligence"])

# Health Check
@app.get("/health", tags=["System Health"])
def health_check():
    return {
        "status": "healthy",
        "service": "Indus Flow Resilience Agent",
        "team": "Indus",
        "hackathon": "Open Agent Hackathon 2026",
        "engine": settings.meterless_engine,
        "model": settings.nvidia_model
    }

@app.get("/api/v1/team", tags=["Team Information"])
def get_team_info():
    return {
        "team_name": "Indus",
        "hackathon": "Open Agent Hackathon 2026",
        "track": "Autonomous Workflow Agents / Enterprise Resilience",
        "members": [
            {"name": "Adarsh Singh", "role": "Team Leader", "focus": "Strategy & Submission"},
            {"name": "Asiya Ali", "role": "PM, DevOps, UI/UX, ML/AI Engineer", "focus": "Architecture, World Model, Docker & UI"},
            {"name": "Gourav Sahu", "role": "Data Scientist & ML/AI Engineer", "focus": "Zetaris Semantic Catalog & Evaluation"},
            {"name": "Raj Singh", "role": "Full-Stack Engineer", "focus": "API Integrations & Testing"}
        ]
    }

# Static Dashboard Setup
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

    @app.get("/", include_in_schema=False)
    def serve_frontend_dashboard():
        index_file = os.path.join(static_dir, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)
        return {"message": "Indus Flow API is running. Access interactive documentation at /docs"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host="0.0.0.0", port=settings.app_port, reload=True)
