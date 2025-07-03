from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse
from sqlalchemy import func, extract
from datetime import datetime, timedelta, date

from app.database import get_db
from app.models import message, contact, inbox
import json

dashboard_route = APIRouter(tags=["Dashboard"])

def _date_from_timestamp(ts):
    return datetime.fromtimestamp(ts).date()

def _filter_messages(db, instance_id=None):
    query = db.query(message)
    if instance_id:
        query = query.filter(message.instanceId == instance_id)
    return query

def _count_messages(db, fromMe_value, start_date: date, end_date: date = None):
    msgs = _filter_messages(db).all()
    count = 0
    for msg in msgs:
        try:
            key_data = json.loads(msg.key) if not isinstance(msg.key, dict) else msg.key
            fromMe = key_data.get("fromMe", False)
            ts_date = _date_from_timestamp(msg.messageTimestamp)
            if fromMe == fromMe_value and (
                (end_date is None and ts_date == start_date) or
                (end_date and start_date <= ts_date <= end_date)
            ):
                count += 1
        except Exception:
            continue
    return count

def _distinct_contacts(db, start_date: date, end_date: date = None):
    msgs = _filter_messages(db).all()
    contacts_set = set()
    for msg in msgs:
        try:
            key_data = json.loads(msg.key) if not isinstance(msg.key, dict) else msg.key
            remoteJid = key_data.get("remoteJid")
            ts_date = _date_from_timestamp(msg.messageTimestamp)
            if remoteJid and (
                (end_date is None and ts_date == start_date) or
                (end_date and start_date <= ts_date <= end_date)
            ):
                contacts_set.add(remoteJid)
        except Exception:
            continue
    return len(contacts_set)

@dashboard_route.get("/dashboard_info")
def get_dashboard_info(db: Session = Depends(get_db)):
    try:
        now = datetime.now()
        today = datetime.now().date()
        week_ago = today - timedelta(days=6)
        month_ago = today - timedelta(days=29)

        # Enviadas (fromMe=True)
        sent_today = _count_messages(db, fromMe_value=True, start_date=today)
        sent_week = _count_messages(db, fromMe_value=True, start_date=week_ago, end_date=today)
        sent_month = _count_messages(db, fromMe_value=True, start_date=month_ago, end_date=today)

        # Recebidas (fromMe=False)
        received_today = _count_messages(db, fromMe_value=False, start_date=today)
        received_week = _count_messages(db, fromMe_value=False, start_date=week_ago, end_date=today)
        received_month = _count_messages(db, fromMe_value=False, start_date=month_ago, end_date=today)

        # Contatos
        total_active_contacts = db.query(func.count(contact.id)).scalar()
        contacts_today = _distinct_contacts(db, start_date=today)
        contacts_week = _distinct_contacts(db, start_date=week_ago, end_date=today)
        contacts_month = _distinct_contacts(db, start_date=month_ago, end_date=today)

        total_inboxes = db.query(func.count(inbox.id)).scalar()

        result = {
            "status": "Success",
            "request_datetime": now.isoformat(),
            "messages_sent": {
                "today": sent_today,
                "last_7_days": sent_week,
                "last_30_days": sent_month,
            },
            "messages_received": {
                "today": received_today,
                "last_7_days": received_week,
                "last_30_days": received_month,
            },
            "contacts": {
                "active": total_active_contacts,
                "talked_today": contacts_today,
                "talked_last_7_days": contacts_week,
                "talked_last_30_days": contacts_month,
            },
            "total_inboxes": total_inboxes,
        }
        return JSONResponse(content=result)
    except Exception as e:
        return JSONResponse(content={"status": "Error", "details": str(e)})

@dashboard_route.get("/dashboard_time")
def get_dashboard_time(db: Session = Depends(get_db)):
    try:
        now = datetime.now()
        today = now.date()

        msgs = db.query(message).all()
        sent_by_hour = [0] * 24
        received_by_hour = [0] * 24

        for msg in msgs:
            try:
                key_data = json.loads(msg.key) if not isinstance(msg.key, dict) else msg.key
                fromMe = key_data.get("fromMe", False)
                ts = msg.messageTimestamp
                ts_date = datetime.fromtimestamp(ts).date()
                if ts_date == today:
                    hour = datetime.fromtimestamp(ts).hour
                    if fromMe:
                        sent_by_hour[hour] += 1
                    else:
                        received_by_hour[hour] += 1
            except Exception:
                continue

        return JSONResponse(content={
            "request_datetime": now.isoformat(),
            "messages_sent_by_hour": [
                {f"time_{h}": sent_by_hour[h]} for h in range(24)
            ],
            "messages_received_by_hour": [
                {f"time_{h}": received_by_hour[h]} for h in range(24)
            ]
        })
    except Exception as e:
        return JSONResponse(content={"status": "Error", "details": str(e)})
