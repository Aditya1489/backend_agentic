from sqlalchemy.orm import Session
from app.models.memory import ConversationHistory, LongTermMemory, UserPreference
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

class MemoryService:
    @staticmethod
    async def get_short_term_memory(db: Session, agent_id: str, session_id: str, limit: int = 10) -> List[dict]:
        """Fetch the most recent messages for the current session."""
        history = db.query(ConversationHistory).filter(
            ConversationHistory.agent_id == agent_id,
            ConversationHistory.session_id == session_id
        ).order_by(ConversationHistory.created_at.desc()).limit(limit).all()
        
        # Return in forward chronological order for the LLM
        return [{"role": h.role, "content": h.content} for h in reversed(history)]

    @staticmethod
    async def add_to_short_term_memory(db: Session, agent_id: str, session_id: str, role: str, content: str):
        """Save a new message to the conversation history."""
        new_entry = ConversationHistory(
            agent_id=agent_id,
            session_id=session_id,
            role=role,
            content=content
        )
        db.add(new_entry)
        db.commit()

    @staticmethod
    async def get_long_term_memory(db: Session, agent_id: str, user_id: Optional[str] = None) -> str:
        """Fetch persistent facts about the user/agent interaction."""
        memories = db.query(LongTermMemory).filter(
            LongTermMemory.agent_id == agent_id,
            (LongTermMemory.user_id == user_id) if user_id else True
        ).all()
        
        if not memories:
            return ""
            
        facts = "\n".join([f"- {m.key}: {m.value}" for m in memories])
        return f"\n\nLong-term Memories:\n{facts}"

    @staticmethod
    async def get_user_preferences(db: Session, agent_id: str, user_id: str) -> str:
        """Fetch specific user preferences."""
        prefs = db.query(UserPreference).filter(
            UserPreference.user_id == user_id,
            UserPreference.agent_id == agent_id
        ).all()
        
        if not prefs:
            return ""
            
        pref_str = "\n".join([f"- {p.preference_key}: {p.preference_value}" for p in prefs])
        return f"\n\nUser Preferences:\n{pref_str}"

    @staticmethod
    async def add_long_term_memory(db: Session, agent_id: str, key: str, value: str, user_id: Optional[str] = None):
        """Save a new fact to long-term memory."""
        # Update if exists, or create new
        existing = db.query(LongTermMemory).filter(
            LongTermMemory.agent_id == agent_id,
            LongTermMemory.user_id == user_id,
            LongTermMemory.key == key
        ).first()
        
        if existing:
            existing.value = value
        else:
            new_entry = LongTermMemory(
                agent_id=agent_id,
                user_id=user_id,
                key=key,
                value=value
            )
            db.add(new_entry)
        db.commit()
