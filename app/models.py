from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.sql import func
from .database import Base

class inbox(Base):
    __tablename__ = "Instance"

    id = Column(String, primary_key=True, index=True)
    ownerJid = Column(String, nullable=False)
    number = Column(String, nullable=False)
    name = Column(String, nullable=False)
    profileName = Column(String, nullable=False)
    token = Column(String, nullable=False)
    createdAt = Column(DateTime, nullable=False)
    updatedAt = Column(DateTime, nullable=False)

class message(Base):
    __tablename__ = "Message"

    id = Column(String, primary_key=True, index=True)
    key = Column(String, nullable=False)
    messageTimestamp = Column(Integer, nullable=False)
    messageType = Column(String, nullable=False)
    message = Column(String, nullable=True)
    instanceId = Column(String, nullable=False)


class contact(Base):
    __tablename__ = "Contact"

    id = Column(String, primary_key=True, index=True)
    remoteJid = Column(String, unique=True, index=True, nullable=False)
    pushName = Column(String, nullable=True)
    instanceId = Column(String, nullable=False)
    createdAt = Column(DateTime(timezone=True), server_default=func.now())
    updatedAt = Column(DateTime(timezone=True), onupdate=func.now())