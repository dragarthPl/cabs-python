from __future__ import annotations
from datetime import datetime
import enum
from typing import Any, Optional

from sqlalchemy import Column, DateTime, String, Enum, Integer, ForeignKey
from sqlalchemy.orm import relationship, backref
from sqlmodel import Field, Relationship

from common.base_entity import BaseEntity


class Claim(BaseEntity, table=True):
    __table_args__ = {'extend_existing': True}

    class Status(enum.Enum):
        DRAFT = 1
        NEW = 2
        IN_PROCESS = 3
        REFUNDED = 4
        ESCALATED = 5
        REJECTED = 6

    class CompletionMode(enum.Enum):
        MANUAL = 1
        AUTOMATIC = 2

    client_id: Optional[int] = Field(default=None, foreign_key="client.id")
    client: Optional['Client'] = Relationship(back_populates="claims")
    transit_id: Optional[Transit] = Field(sa_column=Column(Integer, ForeignKey('transit.id')))
    transit: Optional[Transit] = Relationship(
        sa_relationship=relationship(
            "entity.transit.Transit", backref=backref("claim", uselist=False))
    )
    creation_date: datetime = Field(sa_column=Column(DateTime, nullable=False))
    completion_date: datetime
    change_date: datetime
    reason: str = Field(sa_column=Column(String, nullable=False))
    incident_description: str
    completion_mode: CompletionMode = Field(sa_column=Column(Enum(CompletionMode)))
    status: Status = Field(sa_column=Column(Enum(Status), nullable=False))
    claim_no: str = Field(sa_column=Column(String, nullable=False))
