from fastapi import (
    APIRouter,
    Depends,
    Query,
    Request,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import datetime
import json

from app.database import get_db
from app.models import message, contact
from app.websocket_manager import connection_manager

message_route = APIRouter(tags=["Message"])
manager = connection_manager()

async def _broadcast(payload: dict) -> None:
    await manager.broadcast(json.dumps(payload))

async def _handle_text_message(
    db: Session,
    *,
    instance_id: str,
    message_id: str,
    whatsapp_id: str,
    message_type: str,
    pushname: str,
    datetime_obj: datetime,
    content: str,
    key_data: dict
) -> None:
    msg = message(
        id=message_id,
        key=json.dumps(key_data),
        messageTimestamp=int(datetime_obj.timestamp()),
        messageType=message_type,
        message=content,
        instanceId=instance_id,
    )
    db.add(msg)
    await _broadcast(
        {
            "id": message_id,
            "remoteJid": key_data.get("remoteJid"),
            "fromMe": key_data.get("fromMe"),
            "messageType": message_type,
            "message": content,
            "contact": pushname,
            "timestamp": int(datetime_obj.timestamp()),
            "datetime": datetime_obj.isoformat()
        }
    )

@message_route.websocket("/ws/mensagens")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@message_route.get("/messages")
def get_messages(
    instanceId: str = Query(...),
    contact_number: str = Query(...),
    # padrão 100, mínimo 1, máximo 500
    messages: int = Query(100, ge=1, le=500),  
    db: Session = Depends(get_db)
):
    try:
        whatsapp_id = f"{contact_number}@s.whatsapp.net"
        msgs = (
            db.query(message)
            .filter(
                message.instanceId == instanceId
            )
            .order_by(message.messageTimestamp.asc())
            .all()
        )

        all_messages = []
        for msg in msgs:
            key_data = None
            try:
                key_data = json.loads(msg.key) if not isinstance(msg.key, dict) else msg.key
            except Exception:
                key_data = {}
            remoteJid = key_data.get("remoteJid")
            if remoteJid != whatsapp_id:
                continue  # Só queremos mensagens do contato buscado
            contact_obj = db.query(contact).filter(contact.remoteJid == whatsapp_id).first()
            all_messages.append({
                "type": "text",
                "id": msg.id,
                "remoteJid": remoteJid,
                "fromMe": key_data.get("fromMe"),
                "messageType": msg.messageType,
                "message": msg.message,
                "contact": contact_obj.pushName if contact_obj else "",
                "timestamp": msg.messageTimestamp,
                "datetime": datetime.fromtimestamp(msg.messageTimestamp).isoformat() if msg.messageTimestamp else None
            })
        return JSONResponse(content={"status": "Success", "count": len(all_messages) , "messages": all_messages})
    except Exception as e:
        return JSONResponse(content={"status": "Error", "details": str(e)})

@message_route.post("/wh/messages")
async def webhook_mensagens(request: Request, db: Session = Depends(get_db)):
    data = await request.json()
    try:
        data_block = data.get('data', {})
        instanceId = data_block.get('instanceId')
        messageId = data_block.get('key', {}).get('id')
        WhatsappjId = data_block.get('key', {}).get('remoteJid')
        fromMe = data_block.get('key', {}).get('fromMe', False)
        Message_Type = "Outgoing" if fromMe else "Incoming"
        pushname = data_block.get('pushName')
        message_data = data_block.get('message', {})
        timestamp_unix = data_block.get('messageTimestamp')
        datetime_obj = datetime.fromtimestamp(timestamp_unix) if timestamp_unix else datetime.now()
        key_data = data_block.get('key', {})
        if "conversation" in message_data:
            content = message_data.get("conversation", "")
            await _handle_text_message(
                db,
                instance_id=instanceId,
                message_id=messageId,
                whatsapp_id=WhatsappjId,
                message_type=Message_Type,
                pushname=pushname,
                datetime_obj=datetime_obj,
                content=content,
                key_data=key_data
            )
        db.commit()
        return {"status": "success"}
    except IntegrityError as e:
        db.rollback()
        return {"status": "error", "details": str(e)}
    except Exception as e:
        db.rollback()
        return {"status": "error", "details": str(e)}
