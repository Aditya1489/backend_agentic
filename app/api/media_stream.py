import json
import base64
import asyncio
import websockets
import audioop
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.core import config
from twilio.twiml.voice_response import VoiceResponse, Connect, Stream

router = APIRouter()

@router.websocket("/media-stream")
async def handle_media_stream(websocket: WebSocket):
    await websocket.accept()
    print("Twilio connected to media stream")

    stream_sid = None
    agent_id = None

    try:
        # 1. Handshake with Twilio
        async for message in websocket.iter_text():
            data = json.loads(message)
            event_type = data.get('event')
            
            if event_type == 'start':
                stream_sid = data['start']['streamSid']
                custom_params = data['start'].get('customParameters', {})
                agent_id = custom_params.get('agent_id')
                print(f"Twilio: Stream started: {stream_sid}, Agent ID: {agent_id}")
                
                if not agent_id:
                    print("Error: No agent_id found in customParameters")
                    await websocket.close()
                    return 
                
                break 
                
            elif event_type == 'stop':
                print("Twilio: Stream stopped before start")
                return

    except Exception as e:
        print(f"Error checking start event: {e}")
        await websocket.close()
        return

    elevenlabs_url = f"wss://api.elevenlabs.io/v1/convai/conversation?agent_id={agent_id}"
    print(f"Connecting to ElevenLabs: {elevenlabs_url}")

    try:
        async with websockets.connect(
            elevenlabs_url, 
            additional_headers={"xi-api-key": config.MAKE_PLAN_API_KEY}
        ) as elevenlabs_ws:
            print(f"Connected to ElevenLabs Agent: {agent_id}")
            
            # 2. Init ElevenLabs Session with correct config
            init_msg = {
                "type": "conversation_initiation_client_data",
                "conversation_config_override": {
                    "tts": {
                        "output_format": "pcm_16000" # Request linear PCM 16kHz from Agent
                    }
                    # "agent": {
                    #      "prompt":{
                    #         "first_message": "Hello, I am your support agent. How can I help you?"
                    #      },
                    #      "first_message": "Hello, I am your support agent. How can I help you?"
                    # }

                }
            }
            await elevenlabs_ws.send(json.dumps(init_msg))

            # 3. Relay Tasks
            async def receive_from_twilio():
                state = None
                try:
                    async for message in websocket.iter_text():
                        data = json.loads(message)
                        event_type = data.get('event')

                        if event_type == 'media':
                            # Twilio sends: Base64 -> 8kHz u-law
                            audio_data = base64.b64decode(data['media']['payload'])
                            
                            # 1. Decode u-law to Linear PCM (16-bit)
                            pcm_data = audioop.ulaw2lin(audio_data, 2)
                            
                            # 2. Resample 8kHz -> 16kHz
                            # audioop.ratecv(fragment, width, nchannels, inrate, outrate, state[, weightA[, weightB]])
                            # Returns (new_fragment, new_state)
                            pcm_16k, state = audioop.ratecv(pcm_data, 2, 1, 8000, 16000, state)
                            
                            # 3. Base64 encode for ElevenLabs (expects PCM 16kHz if not specified otherwise, but we should be consistent)
                            # Actually, conversational AI usually expects standard formats.
                            # But let's assume it accepts pcm_16000 if we send it raw? 
                            # Or we can send base64 of the pcm_16k.
                            
                            audio_payload = {
                                "user_audio_chunk": base64.b64encode(pcm_16k).decode('utf-8')
                            }
                            await elevenlabs_ws.send(json.dumps(audio_payload))
                            
                        elif event_type == 'stop':
                            print("Twilio: Stream stopped")
                            break
                        elif event_type == 'clear':
                             # Twilio buffer cleared
                             state = None
                             pass
                except WebSocketDisconnect:
                    print("Twilio disconnected")
                except Exception as e:
                    print(f"Error receiving from Twilio: {e}")

            async def receive_from_elevenlabs():
                state = None # State for ratecv
                try:
                    async for message in elevenlabs_ws:
                        data = json.loads(message)
                        event_type = data.get("type")

                        if event_type == "audio":
                            # Agent sends: Base64 -> PCM 16kHz (requested in init)
                            audio_chunk = data.get("audio_event", {}).get("audio_base_64")
                            if audio_chunk and stream_sid:
                                pcm_16k = base64.b64decode(audio_chunk)
                                
                                # 1. Resample 16kHz -> 8kHz
                                pcm_8k, state = audioop.ratecv(pcm_16k, 2, 1, 16000, 8000, state)
                                
                                # 2. Encode Linear PCM -> u-law
                                ulaw_data = audioop.lin2ulaw(pcm_8k, 2)
                                
                                # 3. Base64 encode for Twilio
                                twilio_payload = base64.b64encode(ulaw_data).decode('utf-8')
                                
                                await websocket.send_json({
                                    "event": "media",
                                    "streamSid": stream_sid, 
                                    "media": {
                                        "payload": twilio_payload
                                    }
                                })
                        
                        elif event_type == "interruption":
                            print("User interrupted AI, clearing stream buffer")
                            if stream_sid:
                                await websocket.send_json({
                                    "event": "clear",
                                    "streamSid": stream_sid 
                                })
                            state = None
                        
                        elif event_type == "ping":
                            if data.get("ping_event", {}).get("event_id"):
                                event_id = data["ping_event"]["event_id"]
                                await elevenlabs_ws.send(json.dumps({
                                    "type": "pong",
                                    "event_id": event_id
                                }))

                except Exception as e:
                    print(f"Error receiving from ElevenLabs: {e}")

            task1 = asyncio.create_task(receive_from_twilio())
            task2 = asyncio.create_task(receive_from_elevenlabs())
            
            print("Starting bidirectional stream...")
            done, pending = await asyncio.wait(
                [task1, task2], 
                return_when=asyncio.FIRST_COMPLETED
            )
            print(f"Stream tasks finished. Done: {len(done)}, Pending: {len(pending)}")
            for task in done:
                 try:
                     task.result()
                 except Exception as e:
                     print(f"Task finished with error: {e}")
            
            for task in pending:
                task.cancel()

    except Exception as e:
        print(f"Connection error with ElevenLabs: {e}")
    finally:
        print("Session closed")
