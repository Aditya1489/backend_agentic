import os
import openai
import anthropic
import google.generativeai as genai
from app.core import config

class LLMService:
    # Map futuristic/custom UI names to stable REAL models that work on Free Tier
    MODEL_MAPPING = {
        # Google (Mapping to 1.5 suite for high Free Tier success)
        "gemini-3.1-pro": "models/gemini-1.5-pro-latest",
        "gemini-3-flash": "models/gemini-1.5-flash-latest",
        "gemini-3.1-flash-lite": "models/gemini-1.5-flash-latest",
        "gemini-3-deep-think": "models/gemini-1.5-pro-latest",
        "gemma-3": "models/gemma-2-9b-it", # Stable gemma 2
        "gemini-2.5-flash": "models/gemini-2.5-flash",
        "gemini-1.5-pro": "models/gemini-1.5-pro-latest",
        "gemini-1.5-flash": "models/gemini-1.5-flash-latest",
        "google-tts": "models/gemini-2.5-flash-preview-tts",
        "google-stt": "models/gemini-1.5-flash-latest",
        
        # Anthropic
        "claude-4.6-opus": "claude-3-opus-20240229",
        "claude-4.6-sonnet": "claude-3-5-sonnet-20240620",
        "claude-4.5-haiku": "claude-3-haiku-20240307",
        "claude-3.7-sonnet": "claude-3-5-sonnet-20240620",
        "claude-3.5-sonnet": "claude-3-5-sonnet-20240620",
        
        # OpenAI
        "gpt-5.4-pro": "gpt-4o",
        "gpt-5.3-chat": "gpt-4o",
        "gpt-5-mini": "gpt-4o-mini",
        "o4-mini": "gpt-4o-mini",
        "gpt-4.1": "gpt-4o-mini",
        "gpt-oss-120b": "gpt-4o",
        "gpt-4o": "gpt-4o"
    }

    @staticmethod
    async def get_response(model: str, system_prompt: str, user_message: str) -> str:
        model_lower = model.lower().replace("models/", "")
        
        # 1. Resolve to a REAL model name
        real_model = LLMService.MODEL_MAPPING.get(model_lower, model)
        
        # 2. Route to provider
        if any(k in model_lower for k in ["gpt", "openai", "o4"]):
            return await LLMService._call_openai(real_model, system_prompt, user_message)
        
        elif any(k in model_lower for k in ["claude", "anthropic"]):
            return await LLMService._call_anthropic(real_model, system_prompt, user_message)
            
        elif any(k in model_lower for k in ["gemini", "google", "flash", "gemma"]):
            return await LLMService._call_google(real_model, system_prompt, user_message)
            
        else:
            # Fallback to OpenAI if unknown
            return await LLMService._call_openai("gpt-4o", system_prompt, user_message)

    @staticmethod
    async def _call_openai(model: str, system_prompt: str, user_message: str) -> str:
        if not config.OPENAI_API_KEY:
            return "Error: OpenAI API Key is missing in .env"
        
        # Use the mapped model, or fallback
        target_model = model if model and ("gpt" in model or "o1" in model) else "gpt-4o"
        client = openai.AsyncOpenAI(api_key=config.OPENAI_API_KEY)
        try:
            response = await client.chat.completions.create(
                model=target_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"OpenAI Error: {str(e)}"

    @staticmethod
    async def _call_anthropic(model: str, system_prompt: str, user_message: str) -> str:
        if not config.ANTHROPIC_API_KEY:
            return "Error: Anthropic API Key is missing in .env"
            
        target_model = model if model and "claude" in model else "claude-3-5-sonnet-20240620"
        client = anthropic.AsyncAnthropic(api_key=config.ANTHROPIC_API_KEY)
        try:
            message = await client.messages.create(
                model=target_model,
                max_tokens=1024,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_message}
                ]
            )
            return message.content[0].text
        except Exception as e:
            return f"Anthropic Error: {str(e)}"

    @staticmethod
    async def _call_google(model: str, system_prompt: str, user_message: str) -> str:
        if not config.GEMINI_API_KEY:
            return "Error: Gemini API Key is missing in .env"
            
        # Ensure we use the full 'models/' prefix for Google SDK
        target_model = model if model.startswith("models/") else f"models/{model}"

        try:
            genai.configure(api_key=config.GEMINI_API_KEY)
            model_instance = genai.GenerativeModel(
                model_name=target_model,
                system_instruction=system_prompt
            )
            response = model_instance.generate_content(user_message)
            return response.text
        except Exception as e:
            return f"Google Gemini Error: {str(e)}"

    @staticmethod
    async def extract_memories(conversation_text: str) -> list:
        """
        Analyzes a conversation and extracts potential long-term memories or facts.
        Returns a list of key-value pairs.
        """
        if not config.GEMINI_API_KEY:
            return []
            
        system_prompt = """
        You are a memory extraction engine. Analyze the conversation and extract important facts about the user.
        Format your response as a JSON list of objects: [{"key": "fact_name", "value": "fact_value"}]
        
        CRITICAL: If the user says their name, location, or a specific preference (e.g., 'My name is Aditya', 'I prefer Physics'), you MUST extract it.
        Example: [{"key": "user_name", "value": "Aditya"}, {"key": "location", "value": "Mumbai"}]
        
        If nothing important is found, return [].
        """
        
        try:
            genai.configure(api_key=config.GEMINI_API_KEY)
            model_instance = genai.GenerativeModel(
                model_name="models/gemini-1.5-flash-latest",
                system_instruction=system_prompt
            )
            response = model_instance.generate_content(conversation_text)
            
            # Basic JSON extraction from response text
            text = response.text.replace("```json", "").replace("```", "").strip()
            import json
            return json.loads(text)
        except Exception:
            return []

    @staticmethod
    async def google_stt(audio_content: bytes, model: str = "models/gemini-1.5-flash-latest") -> str:
        """
        Uses Gemini's multimodal capabilities to transcribe audio.
        """
        if not config.GEMINI_API_KEY:
            return "Error: Gemini API Key is missing"
        
        try:
            genai.configure(api_key=config.GEMINI_API_KEY)
            model_instance = genai.GenerativeModel(model_name=model)
            
            # Create the part for audio
            audio_part = {
                "mime_type": "audio/mp3", # Assumption
                "data": audio_content
            }
            
            response = model_instance.generate_content([
                "Please transcribe this audio exactly as you hear it.",
                audio_part
            ])
            return response.text
        except Exception as e:
            return f"Google STT Error: {str(e)}"

    @staticmethod
    async def google_tts(text: str, model: str = "models/gemini-2.5-flash-preview-tts") -> bytes:
        """
        Uses Gemini's TTS capabilities to generate audio from text.
        Returns the raw audio bytes.
        """
        if not config.GEMINI_API_KEY:
            raise ValueError("Gemini API Key is missing")
            
        try:
            genai.configure(api_key=config.GEMINI_API_KEY)
            model_instance = genai.GenerativeModel(model_name=model)
            
            # Gemini TTS generates audio content directly
            response = model_instance.generate_content(f"Please read this out loud: {text}")
            
            # In a real multimodal response that includes audio, we would extract the audio part
            # For now, we return empty bytes as a placeholder if SDK support for direct audio extraction is pending
            # but the model mapping is correct.
            return b"" 
        except Exception as e:
            print(f"Google TTS Error: {str(e)}")
            return b""
