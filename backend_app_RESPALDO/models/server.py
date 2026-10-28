from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.dialects.postgresql import INET

from app.database.connection import Base


class Server(Base):
    __tablename__ = "servers"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(
        String(100),
        nullable=False
    )

    ip_address = Column(
        INET,
        nullable=False
    )

    status = Column(
        String(30),
        nullable=False,
        default="offline"
    )

    agent = Column(
        String(50),
        nullable=True
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )

    last_seen = Column(
        DateTime(timezone=True),
        nullable=True
    )