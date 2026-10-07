from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, DateTime

from app.database.connection import Base


class Incident(Base):
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, nullable=False)
    status = Column(String(30), nullable=False)
    severity = Column(String(20), nullable=False)

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )