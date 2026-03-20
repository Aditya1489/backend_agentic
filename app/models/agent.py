from sqlalchemy import Column, Integer, String, Text, JSON, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.db.session import Base

class Agent(Base):
    __tablename__ = "agents"

    id = Column(String(255), primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    role = Column(String(255), default="AI Assistant")
    version = Column(String(50), default="1.0.0")
    confidence_score = Column(Integer, default=100)
    status = Column(String(50), default="active") # active, inactive, draft, error
    deployment_status = Column(String(50), default="not_deployed") # deployed, pending, not_deployed
    environment = Column(String(50), default="draft") # draft, test, prod
    config = Column(JSON, nullable=True) # Stores the full canvas state (nodes, edges)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_deployed_at = Column(DateTime(timezone=True), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"))
