from fastapi import APIRouter, HTTPException, Depends
from app.schemas.outbound import OutboundCallRequest
from app.services.twilio_service import TwilioService
from app.core import config

router = APIRouter()

@router.post("/call")
async def initiate_call(request: OutboundCallRequest):
    twilio_service = TwilioService()
    
    print(f"Initiating outbound call for agent: {request.agent_id} to number: {request.phone_number}")
    
    try:
        # Initiate the call via Twilio using the standardized service
        call_sid = twilio_service.initiate_outbound_call(
            to_number=request.phone_number,
            agent_id=request.agent_id,
            api_key=config.MAKE_PLAN_API_KEY
        )
        return {"message": "Call initiated successfully", "call_sid": call_sid}
    except Exception as e:
        # Log the full error but return a clean message to the client
        error_msg = str(e)
        if "unverified" in error_msg.lower() and "trial accounts" in error_msg.lower():
            raise HTTPException(
                status_code=400, 
                detail="Twilio Trial Account Error: The recipient number is unverified. Please verify the number in your Twilio console or upgrade your account."
            )
        print(f"Error initiating call: {e}")
        raise HTTPException(status_code=500, detail=error_msg)

@router.get("/status/{call_sid}")
async def get_call_status(call_sid: str):
    twilio_service = TwilioService()
    try:
        status = twilio_service.get_call_status(call_sid)
        return {"call_sid": call_sid, "status": status}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
