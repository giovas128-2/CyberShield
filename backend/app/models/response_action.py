from datetime import datetime, timezone

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)

from app.database.connection import Base


class ResponseAction(Base):
    __tablename__ = "response_actions"

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

    action_type = Column(
        String(40),
        nullable=False,
    )

    target = Column(
        String(255),
        nullable=True,
    )

    status = Column(
        String(20),
        nullable=False,
        default="pending",
    )

    reversible = Column(
        Boolean,
        nullable=False,
        default=True,
    )

    duration_seconds = Column(
        Integer,
        nullable=True,
    )

    reason = Column(
        Text,
        nullable=False,
    )

    result = Column(
        Text,
        nullable=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    executed_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    rolled_back_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )