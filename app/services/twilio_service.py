from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Connect, Stream
from app.core import config
from typing import Optional

class TwilioService:
    def __init__(self):
        self.client = Client(config.TWILIO_ACCOUNT_SID, config.TWILIO_AUTH_TOKEN)
        self.phone_number = config.TWILIO_PHONE_NUMBER

    def initiate_outbound_call(self, to_number: str, agent_id: str, api_key: str):
        """
        Initiates an outbound call and connects it to the Backend Media Stream Proxy.
        :param to_number: The recipient's phone number.
        :param agent_id: The ElevenLabs agent ID.
        :param api_key: The ElevenLabs API key (unused in TwiML, handled in proxy).
        """
        if not config.NGROK_URL:
            print("Error: NGROK_URL is not set in configuration.")
            # In a real app we might raise an error, but here let's log and maybe fail gracefully or fallback
            # We need the public URL for Twilio to connect to our websocket.
            # Let's assume the user will set it.
            pass

        response = VoiceResponse()
        # Add a short pause
        response.pause(length=1)
        
        connect = Connect()
        # Point to our backend proxy using the public ngrok hostname
        # WebSocket URL: wss://<ngrok-id>.ngrok-free.app/media-stream?agent_id={agent_id}
        
        # Ensure NGROK_URL doesn't have http/https prefix for wss construction if needed, 
        # or just replacing http with wss.
        base_url = config.NGROK_URL.replace("https://", "").replace("http://", "")
        stream_url = f"wss://{base_url}/media-stream"
        
        stream = Stream(url=stream_url)
        # Pass agent_id as a custom parameter. This is more reliable than query params for Twilio Streams.
        stream.parameter(name="agent_id", value=agent_id)
        
        connect.append(stream)
        response.append(connect)
        
        twiml_str = str(response)

        print(f"TwilioService: Initiating call with TwiML:\n{twiml_str}")

        call = self.client.calls.create(
            twiml=twiml_str,
            to=to_number,
            from_=self.phone_number
        )
        return call.sid

    def get_call_status(self, call_sid: str):
        call = self.client.calls(call_sid).fetch()
        return call.status
