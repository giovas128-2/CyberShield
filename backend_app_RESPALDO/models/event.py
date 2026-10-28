from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import INET, JSONB

from app.database.connection import Base


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)

    event_type = Column(String(100), nullable=False)
    source = Column(String(50), nullable=True)
    severity = Column(String(20), nullable=False)

    source_ip = Column(INET, nullable=True)

    description = Column(Text, nullable=True)

    details = Column(JSONB, nullable=True)

    # NUEVO: servidor relacionado con el evento
    server_id = Column(
        Integer,
        ForeignKey("servers.id", ondelete="RESTRICT"),
        nullable=True,
    )

    # NUEVO:
    # BLOCKED = detenido antes de producir efecto
    # REACHED = llegó al servidor, sin impacto comprobado
    # IMPACT = produjo un efecto comprobable
    scope = Column(
        String(10),
        nullable=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )