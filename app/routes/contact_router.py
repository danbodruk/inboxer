from fastapi import APIRouter, Depends, Query, Body, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import contact

contact_route = APIRouter(prefix="/contacts", tags=["Contact"])

@contact_route.get("/")
def get_contacts(instanceId: str = Query(...), db: Session = Depends(get_db)):
    try:
        contacts = db.query(contact).filter(contact.instanceId == instanceId).all()
        result = [
            {
                "contactId": contact.id,
                "WhatsappjId": contact.remoteJid,
                "Whatsapp_num": contact.remoteJid.split('@')[0],
                "pushName": contact.pushName,
                "instanceId": contact.instanceId,
                "createdAt": contact.createdAt.isoformat() if contact.createdAt else None,
                "updatedAt": contact.updatedAt.isoformat() if contact.updatedAt else None
            }
            for contact in contacts
        ]
        return JSONResponse(content={"status": "Success", "count": len(result), "contacts": result})
    except Exception as e:
        return JSONResponse(content={"status": "Error", "details": str(e)})

@contact_route.post("/")
def create_contact(
    pushname: str = Body(...),
    WhatsappjId: str = Body(...),
    instanceId: str = Body(...),
    db: Session = Depends(get_db)
):
    try:
        # Buscar duplicidade com os nomes corretos dos campos!
        exists = db.query(contact).filter(contact.remoteJid == WhatsappjId, contact.instanceId == instanceId).first()
        if exists:
            return JSONResponse(content={"status": "Error", "details": "Contact already exists"})
        import uuid
        # Criar o contato usando os nomes corretos dos campos do model!
        new_contact = contact(
            id=str(uuid.uuid4()),
            remoteJid=WhatsappjId,
            pushname=pushname,
            instanceId=instanceId
        )
        db.add(new_contact)
        db.commit()
        db.refresh(new_contact)
        return JSONResponse(content={
            "status": "Success",
            "contact": {
                "contactId": new_contact.id,
                "pushname": new_contact.pushName,
                "WhatsappjId": new_contact.remoteJid,
                "instanceId": new_contact.instanceId,
                "createdAt": new_contact.createdAt.isoformat() if new_contact.createdAt else None
            }
        })
    except Exception as e:
        db.rollback()
        return JSONResponse(content={"status": "Error", "details": str(e)})


@contact_route.delete("/")
def delete_contact(contactId: str = Query(...), db: Session = Depends(get_db)):
    try:
        # Buscar usando o campo id correto!
        contact_obj = db.query(contact).filter(contact.id == contactId).first()
        if not contact_obj:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"status": "Error", "details": "Contact not found"}
            )
        db.delete(contact_obj)
        db.commit()
        return JSONResponse(content={"status": "Success", "message": f"Contact {contactId} deleted"})
    except Exception as e:
        db.rollback()
        return JSONResponse(content={"status": "Error", "details": str(e)})
