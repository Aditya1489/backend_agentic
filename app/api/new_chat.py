
from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
from typing import Optional
import json
import websockets
import asyncio
from app.core import config
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

class ChatRequest(BaseModel):
    agent_id: str
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str

@router.post("/chat/new", response_model=ChatResponse)
async def chat_with_agent_new(request: ChatRequest = Body(...)):
    """
    New chat flow using a transient WebSocket connection to simulate a RESTful text-chat experience.
    This bypasses the ElevenLabs SDK's missing conversational features by directly interacting with the Agent protocol.
    """
    agent_url = f"wss://api.elevenlabs.io/v1/convai/conversation?agent_id={request.agent_id}"
    response_text = ""
    
    logger.info(f"Starting new chat session with agent {request.agent_id}")
    
    try:
        async with websockets.connect(
            agent_url,
            additional_headers={"xi-api-key": config.MAKE_PLAN_API_KEY}
        ) as ws:
            # 1. Send Initial Configuration (Enable TTS to get transcript, ignore audio)
            await ws.send(json.dumps({
                "type": "conversation_initiation_client_data",
                "conversation_config_override": {
                    "agent": {
                        "first_message": " " # Suppress default greeting so we only get response to our input
                    },
                    "tts": {
                        "mode": "default" 
                    }
                }
            }))

            # 2. Send User Message
            await ws.send(json.dumps({
                "text": request.message,
                "try_trigger_generation": True
            }))
            
            logger.info(f"Sent message to agent: {request.message}")

            # 3. Listen for Response (Transient Mode)
            # We listen until we get a complete response or timeout.
            try:
                async with asyncio.timeout(15.0): # Generous timeout for agent thinking
                    async for message in ws:
                        # logger.info(f"Received raw message: {message}")
                        
                        try:
                            data = json.loads(message)
                        except json.JSONDecodeError:
                            logger.error("Failed to decode JSON message")
                            continue

                        logger.info(f"Parsed data type: {type(data)}")
                        
                        if not isinstance(data, dict):
                                logger.warning(f"Received non-dict data: {data}")
                                continue

                        event_type = data.get("type", "")
                        
                        # logger.info(f"WS Event: {event_type}")


                        if event_type == "agent_response":
                            agent_resp = data.get("agent_response_event", {}).get("agent_response", {})
                            
                            # Handle direct string response (some agents return plain text here)
                            if isinstance(agent_resp, str):
                                response_text += agent_resp + " "
                            # Handle structured response (usual format)
                            elif isinstance(agent_resp, dict):
                                text_content = agent_resp.get("metadata", {}).get("transcript")
                                if text_content:
                                    response_text += text_content + " "
                            
                            if "text" in data:
                                response_text += data["text"] + " "

                        # Optimization: If we got text from the main response event, we can break early
                        # The 'agent_response' usually contains the full answer for text mode
                        if response_text.strip():
                            logger.info(f"Captured text, finishing early: '{response_text.strip()}'")
                            break

                        if event_type == "agent_response_completed":
                            logger.info(f"Agent response completed. Captured: '{response_text.strip()}'")
                            break
                                
            except asyncio.TimeoutError:
                logger.warning("Agent response timed out.")
                # If we have partial text, return it. If not, error.
                pass

    except Exception as e:
        logger.error(f"Chat Error: {e}")
        # Return a friendly error if connection fails entirely
        return ChatResponse(response="I'm having trouble connecting to the agent right now. Please try again.")

    if not response_text:
        return ChatResponse(response="[Voice Agent replied but no text transcript was captured]")

    return ChatResponse(response=response_text.strip())
