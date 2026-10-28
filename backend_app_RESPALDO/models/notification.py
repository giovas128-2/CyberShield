from datetime import datetime, timezone

from sqlalchemy import BigInteger, Column, Integer, String, Text, DateTime, ForeignKey

from app.database.connection import Base


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    incident_id = Column(
        Integer,
        ForeignKey("incidents.id", ondelete="RESTRICT"),
        nullable=False,
    )

    recipient = Column(
        String(255),
        nullable=False,
    )

    channel = Column(
        String(30),
        nullable=False,
        default="dashboard",
    )

    status = Column(
        String(20),
        nullable=False,
        default="pending",
    )

    message = Column(
        Text,
        nullable=False,
    )

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    sent_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )