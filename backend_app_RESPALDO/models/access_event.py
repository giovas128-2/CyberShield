from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import INET, JSONB
from app.database.connection import Base


class AccessEvent(Base):
    __tablename__ = "access_events"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=True,
    )

    device_id = Column(
        Integer,
        ForeignKey("devices.id", ondelete="RESTRICT"),
        nullable=True,
    )

    session_id = Column(
        Integer,
        ForeignKey("sessions.id", ondelete="RESTRICT"),
        nullable=True,
    )

    event_type = Column(String(100), nullable=False)
    decision = Column(String(30), nullable=False)
    severity = Column(String(20), nullable=False)
    source_ip = Column(INET, nullable=True)
    details = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())