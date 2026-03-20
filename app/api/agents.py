from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
from app.services.agent_service import AgentService
from app.db.session import get_db
from sqlalchemy.orm import Session
from app.models.agent import Agent as AgentModel
from app.schemas.agent import AgentCreate, AgentResponse

router = APIRouter()

@router.get("/", response_model=List[Dict[str, Any]])
async def get_agents(db: Session = Depends(get_db)):
    # 1. Fetch from database first
    db_agents = db.query(AgentModel).all()
    results = []
    for agent in db_agents:
        results.append({
            "id": agent.id,
            "name": agent.name,
            "description": agent.description,
            "role": agent.role,
            "version": agent.version,
            "status": agent.status,
            "config": agent.config,
            "confidenceScore": agent.confidence_score,
            "environment": agent.environment,
            "deploymentStatus": agent.deployment_status or "deployed",
            "validationStatus": "valid",
            "monthlyCost": 45.0, # Mock costs
            "avgLatency": 1.2,   # Mock latency
            "createdAt": agent.created_at.isoformat() if agent.created_at else None,
            "updatedAt": agent.updated_at.isoformat() if agent.updated_at else None
        })
    
    # 2. Add TwelveLabs/ElevenLabs agents if any (legacy support)
    try:
        agent_service = AgentService()
        external_agents = await agent_service.get_agents()
        results.extend(external_agents)
    except Exception as e:
        print(f"Error fetching external agents: {e}")
        
    return results

@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(agent_id: str, db: Session = Depends(get_db)):
    agent = db.query(AgentModel).filter(AgentModel.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent

@router.post("/", response_model=AgentResponse)
async def create_agent(agent_in: AgentCreate, db: Session = Depends(get_db)):
    # Check if agent already exists
    existing_agent = db.query(AgentModel).filter(AgentModel.id == agent_in.id).first()
    if existing_agent:
        # Update existing agent
        for key, value in agent_in.dict().items():
            setattr(existing_agent, key, value)
        existing_agent.user_id = 1 # Temporary hardcode for dev
        db.commit()
        db.refresh(existing_agent)
        return existing_agent
        
    db_agent = AgentModel(**agent_in.dict())
    db_agent.user_id = 1 # Temporary hardcode for dev
    db.add(db_agent)
    db.commit()
    db.refresh(db_agent)
    return db_agent
