from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc
import json

from app.database import get_db
from app.models import message, contact

conversation_route = APIRouter(tags=["Conversation"])

@conversation_route.get("/conversations")
def get_conversations(
    instanceId: str = Query(...),
    # padrão 25, mínimo 1, máximo 100 (ajuste o máximo que for necessário)
    conversations: int = Query(25, ge=1, le=100),  
    db: Session = Depends(get_db)
):
    try:
        msgs = (
            db.query(message)
            .filter(message.instanceId == instanceId)
            .order_by(desc(message.messageTimestamp))
            .all()
        )

        conversations_dict = {}
        for msg in msgs:
            try:
                if isinstance(msg.key, dict):
                    key_data = msg.key
                else:
                    key_data = json.loads(msg.key)
                remoteJid = key_data.get("remoteJid")
                if (
                    remoteJid and
                    remoteJid.endswith("@s.whatsapp.net") and
                    remoteJid not in conversations_dict
                ):
                    conversations_dict[remoteJid] = {
                        "contact_number": remoteJid.replace("@s.whatsapp.net", ""),
                        "last_message": msg.message,
                        "last_message_type": getattr(msg, "Message_Type", getattr(msg, "messageType", None)),
                        "last_message_timestamp": msg.messageTimestamp,
                        "key_remoteJid": remoteJid,
                        "key_fromMe": key_data.get("fromMe"),
                    }
                    if len(conversations_dict) == conversations:
                        break
            except Exception as e:
                print("Erro ao processar mensagem:", e)
                continue

        remoteJids = list(conversations_dict.keys())
        contatos = db.query(contact).filter(contact.remoteJid.in_(remoteJids)).all()
        contatos_dict = {c.remoteJid: c for c in contatos}

        result = []
        for remoteJid, data in conversations_dict.items():
            contato = contatos_dict.get(remoteJid)
            data.update({
                "contact_id": contato.id if contato else None,
                "contact_name": contato.pushName if contato else None,
                "createdAt": contato.createdAt.isoformat() if contato and contato.createdAt else None,
                "updatedAt": contato.updatedAt.isoformat() if contato and contato.updatedAt else None,
            })
            result.append(data)

        return JSONResponse(content={
            "status": "Success",
            "count": len(result),
            "conversations": result
        })
    except Exception as e:
        return JSONResponse(content={"status": "Error", "details": str(e)})

