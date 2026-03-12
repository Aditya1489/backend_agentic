
from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
from typing import Optional
import json
import websockets
import asyncio
from app.core import config

router = APIRouter()

class ChatRequest(BaseModel):
    agent_id: str
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str

@router.post("/chat", response_model=ChatResponse)
async def chat_with_agent(request: ChatRequest = Body(...)):
    """
    Connects to the ElevenLabs Agent WebSocket to handle text-based conversation.
    Sends user text (if supported) and listens for transcript events to return as response.
    """
    agent_url = f"wss://api.elevenlabs.io/v1/convai/conversation?agent_id={request.agent_id}"
    
    response_text = ""
    
    try:
        async with websockets.connect(
            agent_url,
            additional_headers={"xi-api-key": config.MAKE_PLAN_API_KEY}
        ) as ws:
            # 1. Send Initial Configuration
            # We enable normal generation to ensure we get the transcript. 
            # We will simply ignore the audio data received.
            await ws.send(json.dumps({
                "type": "conversation_initiation_client_data",
                "conversation_config_override": {
                    "tts": {
                         "mode": "default" 
                    }
                }
            }))

            # 2. Send User Text
            # Note: The protocol for direct text input is not officially documented as strictly "text".
            # However, standard JSON payloads often work if the key is right.
            # Let's try sending a "user_transcript" event or similar.
            # Actually, some implementations suggest just sending { "text": "..." } or { "type": "user_message", "message": "..." }
            # Let's try the simplest JSON payload first.
            await ws.send(json.dumps({
                "text": request.message,
                "try_trigger_generation": True
            }))
            
            # 3. Listen for Response
            # We expect `agent_response` or `transcript` events.
            # We will collect text until we detect end of turn (silence or specific event) or timeout.
            

            
            try:
                async with asyncio.timeout(10.0):
                    async for message in ws:
                        data = json.loads(message)
                        print(f"WS Event Received: {json.dumps(data, indent=2)}") # Debug: See what the agent sends
                        event_type = data.get("type", "")
                        
                        if event_type == "agent_response":
                            agent_resp = data.get("agent_response_event", {}).get("agent_response", {})
                            text_content = agent_resp.get("metadata", {}).get("transcript") 
                            if text_content:
                                response_text += text_content + " "
                            
                            if "text" in data:
                                response_text += data["text"] + " "
                        
                        if event_type == "agent_response_completed":
                            print(f"Agent response completed. Captured: '{response_text}'")
                            break
            except asyncio.TimeoutError:
                 print("Response timeout reached.")
                 pass 
                    
    except Exception as e:
        print(f"WS Connection Error: {e}")
    
    if response_text:
        print(f"Captured Agent Response: {response_text.strip()}")
    else:
        print("No text response captured from agent stream.")
    
    if not response_text:
         return ChatResponse(response="[Voice Agent replied but no text transcript was captured from the stream]")

    return ChatResponse(response=response_text.strip())
