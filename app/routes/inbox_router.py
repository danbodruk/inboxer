from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi import Query
from fastapi.responses import JSONResponse
from fastapi import Depends
from fastapi import status
from fastapi import Body
from sqlalchemy.orm import Session
from app.database import get_db
from uuid import uuid4
from app.models import inbox



inbox_route = APIRouter(
    prefix = '/inbox',
    tags = [ 'Inbox' ]
)

# POST Inbox
# @inbox_route.post("/create_inbox")
# def create_inbox(
#     number: str = Body(...),
#     name: str = Body(...),
#     profileName: str = Body(...),
#     token: str = Body(...),
#     db: Session = Depends(get_db)
# ):
#     try:
#         from datetime import datetime
#         ownerJid = f"{number}@s.whatsapp.net"
#         new_inbox = inbox(
#             id=str(uuid4()),
#             ownerJid=ownerJid,
#             number=number,
#             name=name,
#             profileName=profileName,
#             token=token,
#             createdAt=datetime.utcnow(),
#             updatedAt=datetime.utcnow(),
#         )
#         db.add(new_inbox)
#         db.commit()
#         db.refresh(new_inbox)
#         return JSONResponse(content={
#             "status": "Success",
#             "inbox": {
#                 "id": new_inbox.id,
#                 "ownerJid": new_inbox.ownerJid,
#                 "number": new_inbox.number,
#                 "name": new_inbox.name,
#                 "profileName": new_inbox.profileName,
#                 "token": new_inbox.token,
#                 "createdAt": new_inbox.createdAt.isoformat() if new_inbox.createdAt else None,
#                 "updatedAt": new_inbox.updatedAt.isoformat() if new_inbox.updatedAt else None
#             }
#         })
#     except Exception as e:
#         db.rollback()
#         return JSONResponse(content={"status": "Error", "details": str(e)})



# GET Inbox
@inbox_route.get("/")
def get_inbox(db: Session = Depends(get_db)):
    try:
        inboxes = db.query(inbox).all()
        result = [
            {
                
                "instance_id": inbox.id,
                "whatsappjID": inbox.ownerJid,
                "inbox_name": inbox.name,
                "profileName": inbox.profileName,
                "token": inbox.token,
                "createdAt": inbox.createdAt.isoformat() if inbox.createdAt else None,
                "updatedAt": inbox.updatedAt.isoformat() if inbox.updatedAt else None
            }
            for inbox in inboxes
        ]
        return JSONResponse(content={"status": "Success", "count": len(result), "inboxes": result})
    except Exception as e:
        return JSONResponse(content={"status": "Error", "details": str(e)})

# DELETE Inbox
# @inbox_route.delete("/{inbox_id}")
# def delete_inbox(inbox_id: str, db: Session = Depends(get_db)):
#     try:
#         inbox_obj = db.query(inbox).filter(inbox.id == inbox_id).first()
#         if not inbox_obj:
#             return JSONResponse(
#                 status_code=status.HTTP_404_NOT_FOUND,
#                 content={"status": "Error", "details": "Inbox not found"}
#             )
#         db.delete(inbox_obj)
#         db.commit()
#         return JSONResponse(content={"status": "Success", "message": f"Inbox {inbox_id} deleted"})
#     except Exception as e:
#         db.rollback()
#         return JSONResponse(content={"status": "Error", "details": str(e)})
