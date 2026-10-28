from sqlalchemy import Column, Integer, String, DateTime, func
from app.database.connection import Base


class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    device_uuid = Column(String(120), unique=True, nullable=False)
    device_name = Column(String(120), nullable=True)
    platform = Column(String(80), nullable=True)
    status = Column(String(20), nullable=False, default="untrusted")
    first_seen = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    last_seen = Column(DateTime(timezone=True), nullable=False, server_default=func.now())