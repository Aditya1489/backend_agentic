from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
from app.services.agent_service import AgentService

router = APIRouter()

@router.get("/", response_model=List[Dict[str, Any]])
async def get_agents():
    agent_service = AgentService()
    try:
        return await agent_service.get_agents()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
