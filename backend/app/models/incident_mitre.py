from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    ForeignKey,
    Integer,
    String,
    Text,
)

from app.database.connection import Base


class IncidentMitre(Base):
    __tablename__ = "incident_mitre"

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

    technique_id = Column(
        String(20),
        nullable=False,
    )

    technique_name = Column(
        String(150),
        nullable=True,
    )

    tactic = Column(
        String(100),
        nullable=True,
    )

    reference_url = Column(
        Text,
        nullable=True,
    )

    is_primary = Column(
        Boolean,
        nullable=False,
        default=False,
    )

    notes = Column(
        Text,
        nullable=True,
    )
