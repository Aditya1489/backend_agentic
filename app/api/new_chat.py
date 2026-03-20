
from fastapi import APIRouter, HTTPException, Body, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
import json
import websockets
import asyncio
from app.core import config as settings
import logging
from app.db.session import get_db, SessionLocal
from sqlalchemy.orm import Session
from fastapi import Depends
from app.models.agent import Agent as AgentModel
from app.services.llm_service import LLMService
from app.services.memory_service import MemoryService

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
async def chat_with_agent_new(
    background_tasks: BackgroundTasks,
    request: ChatRequest = Body(...),
    db: Session = Depends(get_db)
):
    """
    New chat flow supporting both internal dynamic agents and ElevenLabs agents.
    """
    # 1. Check if agent exists in our database
    db_agent = db.query(AgentModel).filter(AgentModel.id == request.agent_id).first()
    
    if db_agent:
        logger.info(f"Using dynamic agent from database: {db_agent.name} (ID: {request.agent_id})")
        # Ensure tables exist (one-time check in case they were missing)
        from app.db.session import engine, Base
        Base.metadata.create_all(bind=engine)
        
        agent_config = db_agent.config or {}
        nodes = agent_config.get("nodes", [])
        edges = agent_config.get("edges", [])
        
        # 1. Find the LLM node first (this is our "brain")
        llm_node = next((n for n in nodes if n.get("data", {}).get("category") == "llm"), None)
        if not llm_node:
            return ChatResponse(response="This agent is missing an LLM node in its configuration.")
            
        # 2. Find the System Prompt connected to this LLM
        edge_to_llm = next((e for e in edges if e.get("target") == llm_node.get("id")), None)
        
        system_prompt = "You are a helpful assistant."
        if edge_to_llm:
            source_id = edge_to_llm.get("source")
            prompt_node = next((n for n in nodes if n.get("id") == source_id), None)
            if prompt_node and prompt_node.get("data", {}).get("category") == "prompt":
                system_prompt = prompt_node.get("data", {}).get("prompt", system_prompt)
        
        model_name = llm_node.get("data", {}).get("modelId") or llm_node.get("data", {}).get("label", "gpt-4o")

        # 3. Detect Memory Nodes
        has_short_term = any(n for n in nodes if n.get("data", {}).get("category") == "memory" and n.get("type") == "short_term")
        has_long_term = any(n for n in nodes if n.get("data", {}).get("category") == "memory" and n.get("type") == "long_term")
        has_user_pref = any(n for n in nodes if n.get("data", {}).get("category") == "memory" and n.get("type") == "user_memory")
        
        # 4. Gather Memory Context
        session_id = request.session_id or "default_session"
        user_id = "default_user" # In a real app, this would come from the auth token
        
        context_parts = [system_prompt]
        
        if has_long_term:
            lt_memory = await MemoryService.get_long_term_memory(db, request.agent_id, user_id)
            if lt_memory: context_parts.append(lt_memory)
            
        if has_user_pref:
            u_prefs = await MemoryService.get_user_preferences(db, request.agent_id, user_id)
            if u_prefs: context_parts.append(u_prefs)

        final_system_prompt = "\n".join(context_parts)
        # Add a meta-instruction to ensure the model uses the memory
        if has_long_term or has_user_pref:
            final_system_prompt += "\n\nIMPORTANT: You have a long-term memory. Use the information provided above to personalize your responses and acknowledge your previous interactions with the user if relevant."
        
        # 5. Handle Short-term Memory (History)
        messages = []
        if has_short_term:
            history = await MemoryService.get_short_term_memory(db, request.agent_id, session_id)
            messages.extend(history)
            
        # Add current user message to history
        await MemoryService.add_to_short_term_memory(db, request.agent_id, session_id, "user", request.message)
        
        # 6. Get LLM Response with Context
        # Note: get_response currently takes (model, system, user_text). 
        # For full history support, we'd need to update it, but for now let's append history to user prompt if needed.
        full_user_input = request.message
        if has_short_term and history:
            history_str = "\n".join([f"{h['role'].capitalize()}: {h['content']}" for h in history])
            full_user_input = f"Conversation History:\n{history_str}\n\nUser: {request.message}"

        logger.info(f"Truly dynamic chat: Model={model_name}, Memory=[ST:{has_short_term}, LT:{has_long_term}, UP:{has_user_pref}]")
        
        response = await LLMService.get_response(model_name, final_system_prompt, full_user_input)
        
        # Save agent response to history
        if has_short_term:
            await MemoryService.add_to_short_term_memory(db, request.agent_id, session_id, "assistant", response)
            
        # 7. Background Task: Extract New Memories
        if has_long_term or has_user_pref:
            async def extract_and_save(agent_id: str, user_id: str, msg: str, resp: str):
                # Use a fresh session for the background task
                db_task = SessionLocal()
                try:
                    conversation = f"User: {msg}\nAssistant: {resp}"
                    logger.info(f"Extracting memories for agent {agent_id}...")
                    new_facts = await LLMService.extract_memories(conversation)
                    if new_facts:
                        logger.info(f"Extracted {len(new_facts)} new facts: {new_facts}")
                    for fact in new_facts:
                        await MemoryService.add_long_term_memory(db_task, agent_id, fact['key'], fact['value'], user_id)
                except Exception as e:
                    logger.error(f"Error in background memory extraction: {e}")
                finally:
                    db_task.close()
            
            background_tasks.add_task(extract_and_save, request.agent_id, user_id, request.message, response)

        logger.info(f"Final Prompt to LLM: {final_system_prompt[:200]}...")
        return ChatResponse(response=response)

    # 2. Fallback to ElevenLabs (for legacy/external agents)
    agent_url = f"wss://api.elevenlabs.io/v1/convai/conversation?agent_id={request.agent_id}"
    response_text = ""
    # ... (rest of the existing ElevenLabs WebSocket logic)
    
    logger.info(f"Starting new chat session with agent {request.agent_id}")
    
    try:
        async with websockets.connect(
            agent_url,
            additional_headers={"xi-api-key": settings.MAKE_PLAN_API_KEY}
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
                while True:
                    # Use wait_for for compatibility with Python < 3.11
                    try:
                        message = await asyncio.wait_for(ws.recv(), timeout=15.0)
                    except asyncio.TimeoutError:
                        logger.warning("Agent response timed out.")
                        break
                    
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
