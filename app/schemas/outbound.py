from pydantic import BaseModel

class OutboundCallRequest(BaseModel):
    phone_number: str
    agent_id: str
