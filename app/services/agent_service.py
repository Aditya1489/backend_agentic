import httpx
from app.core import config
from typing import List, Dict, Any

class AgentService:
    def __init__(self):
        self.api_key = config.MAKE_PLAN_API_KEY
        self.base_url = "https://api.elevenlabs.io/v1/convai/agents"

    async def get_agents(self) -> List[Dict[str, Any]]:
        print(f"AgentService: Fetching agents from {self.base_url}")
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    self.base_url,
                    headers={"xi-api-key": self.api_key}
                )
                print(f"AgentService: Received response status {response.status_code}")
                response.raise_for_status()
                data = response.json()
                agents = data.get("agents", [])
                print(f"AgentService: Found {len(agents)} agents")
                
                # Map to our internal Agent type format
                return [self._map_agent(agent) for agent in agents]
            except httpx.HTTPStatusError as e:
                print(f"HTTP error occurred: {e.response.status_code} - {e.response.text}")
                raise
            except Exception as e:
                print(f"An error occurred in AgentService: {str(e)}")
                import traceback
                traceback.print_exc()
                raise

    async def get_agent_details(self, agent_id: str) -> Dict[str, Any]:
        """Fetches detailed configuration for a specific agent, including system prompt."""
        url = f"{self.base_url}/{agent_id}"
        print(f"AgentService: Fetching specific agent details from {url}")
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    url,
                    headers={"xi-api-key": self.api_key}
                )
                response.raise_for_status()
                data = response.json()
                return data
            except Exception as e:
                print(f"Error fetching agent details: {str(e)}")
                raise

    def _map_agent(self, ext_agent: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "id": ext_agent.get("agent_id"),
            "name": ext_agent.get("name"),
            "description": f"External agent from Make Plan. Access level: {ext_agent.get('access_level')}",
            "role": "Voice Agent",
            "version": "1.0",
            "confidenceScore": 100,
            "status": "active",
            "deploymentStatus": "deployed",
            "environment": "prod",
            "createdAt": self._unix_to_iso(ext_agent.get("last_updated_at_unix")),
            "updatedAt": self._unix_to_iso(ext_agent.get("last_updated_at_unix")),
            "createdBy": "Make Plan System",
            "allowedActions": [],
            "forbiddenActions": [],
            "risks": [],
            "validationStatus": "valid",
            "monthlyCost": 0,
            "avgLatency": 0,
        }

    def _unix_to_iso(self, unix_time: int) -> str:
        if not unix_time:
            return ""
        from datetime import datetime
        return datetime.fromtimestamp(unix_time).isoformat()
