from __future__ import annotations

import enum
from datetime import datetime
from typing import Optional

from common.base_entity import BaseEntity
from sqlalchemy import Column, DateTime, Enum, Integer, String
from sqlmodel import Field

from crm.claims.status import Status
from money import Money


class Claim(BaseEntity, table=True):
    __table_args__ = {'extend_existing': True}

    class CompletionMode(enum.Enum):
        MANUAL = 1
        AUTOMATIC = 2

    owner_id: Optional[int] = Field(default=0, sa_column=Column(Integer, nullable=True))

    transit_id: Optional[int] = Field(default=0, sa_column=Column(Integer, nullable=True))

    creation_date: Optional[datetime] = Field(sa_column=Column(DateTime, nullable=False))
    completion_date: Optional[datetime]
    change_date: Optional[datetime]
    reason: Optional[str] = Field(sa_column=Column(String, nullable=False))
    incident_description: Optional[str]
    completion_mode: Optional[CompletionMode] = Field(sa_column=Column(Enum(CompletionMode)))
    status: Optional[Status] = Field(sa_column=Column(Enum(Status), nullable=False))
    claim_no: Optional[str] = Field(sa_column=Column(String, nullable=False))

    transit_price: Optional[int] = Field(default=0, sa_column=Column(Integer, nullable=False))

    def escalate(self) -> None:
        self.status = Status.ESCALATED
        self.completion_date = datetime.now()
        self.change_date = datetime.now()
        self.completion_mode = Claim.CompletionMode.MANUAL

    def refund(self) -> None:
        self.status = Status.REFUNDED
        self.completion_date = datetime.now()
        self.change_date = datetime.now()
        self.completion_mode = Claim.CompletionMode.AUTOMATIC

    def get_transit_price(self) -> Money:
        return Money(self.transit_price)

    def set_transit(self, transit_id: int):
        self.transit_id = transit_id

    def set_transit_price(self, transit_price: Money) -> None:
        self.transit_price = transit_price.to_int()

    def __eq__(self, o):
        if not isinstance(o, Claim):
            return False
        return self.id is not None and self.id == o.id
