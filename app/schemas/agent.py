from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class AgentCreate(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    role: Optional[str] = "AI Assistant"
    version: Optional[str] = "1.0.0"
    config: Dict[str, Any]
    status: Optional[str] = "active"
    environment: Optional[str] = "draft"

class AgentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    status: Optional[str] = None

class AgentResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    role: str
    version: str
    status: str
    config: Dict[str, Any]
    created_at: Optional[Any] = None
    updated_at: Optional[Any] = None
    
    class Config:
        from_attributes = True
