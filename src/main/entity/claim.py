from __future__ import annotations

import enum
from datetime import datetime
from typing import Any, Optional

from common.base_entity import BaseEntity
from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import backref, relationship
from sqlmodel import Field, Relationship


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

    # @ManyToOne
    owner_id: Optional[int] = Field(default=None, foreign_key="client.id")
    owner: Optional[Client] = Relationship(
        sa_relationship=relationship(
            "entity.client.Client", back_populates="claims")
    )

    # @OneToOne
    transit_id: Optional[int] = Field(sa_column=Column(Integer, ForeignKey('transit.id')))
    transit: Optional[Transit] = Relationship(
        sa_relationship=relationship(
            "entity.transit.Transit", backref=backref("claim", uselist=False))
    )
    creation_date: datetime = Field(sa_column=Column(DateTime, nullable=False))
    completion_date: Optional[datetime]
    change_date: Optional[datetime]
    reason: str = Field(sa_column=Column(String, nullable=False))
    incident_description: Optional[str]
    completion_mode: Optional[CompletionMode] = Field(sa_column=Column(Enum(CompletionMode)))
    status: Status = Field(sa_column=Column(Enum(Status), nullable=False))
    claim_no: str = Field(sa_column=Column(String, nullable=False))

    def __eq__(self, o):
        if not isinstance(o, Claim):
            return False
        return self.id is not None and self.id == o.id