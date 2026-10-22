"""Indus Flow: Autonomous Supply Chain Resilience Agent API."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from src.agents.resilience_agent import SupplyChainResilienceAgent
from src.engines.world_model import WorldState
from src.config import settings

app = FastAPI(
    title="Indus Flow — Open Agent Hackathon 2026",
    description="Autonomous Supply Chain Resilience Agent integrating Meterless World Model, Zetaris, and NVIDIA NIM.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

agent = SupplyChainResilienceAgent()

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "team": "Indus",
        "hackathon": "Open Agent Hackathon 2026",
        "engine": settings.meterless_engine,
        "model": settings.nvidia_model
    }

@app.get("/api/v1/team")
def get_team_info():
    return {
        "team_name": "Indus",
        "members": [
            {"name": "Adarsh Singh", "role": "Leader"},
            {"name": "Asiya Ali", "role": "PM, DevOps, UI/UX, ML/AI Engineer"},
            {"name": "Gourav Sahu", "role": "Data Scientist, ML/AI Engineer"},
            {"name": "Raj Singh", "role": "Full-Stack Engineer"}
        ],
        "project": "Indus Flow",
        "track": "Autonomous Workflow Agents / Enterprise Resilience"
    }

@app.post("/api/v1/agent/run")
async def run_resilience_cycle():
    """Trigger complete sense-simulate-decide-act agent workflow."""
    try:
        result = await agent.execute_resilience_cycle()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host="0.0.0.0", port=settings.app_port, reload=True)
