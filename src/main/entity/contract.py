from __future__ import annotations

import enum
from datetime import datetime
from typing import Set, Optional

from sqlalchemy import Column, DateTime, Enum, String
from sqlalchemy.orm import relationship
from sqlmodel import Field, Relationship

from common.base_entity import BaseEntity


class Contract(BaseEntity, table=True):
    __table_args__ = {'extend_existing': True}

    class Status(enum.Enum):
        NEGOTIATIONS_IN_PROGRESS = 1
        REJECTED = 2
        ACCEPTED = 3

    # @OneToMany(mappedBy = "contract")
    attachments: Set[ContractAttachment] = Relationship(
        sa_relationship=relationship(
            "entity.contract_attachment.ContractAttachment", back_populates="contract")
    )
    partner_name: Optional[str]
    subject: Optional[str]
    # @Column(nullable=false)
    creation_date: datetime = Field(default=datetime.now(), sa_column=Column(DateTime, nullable=False))
    accepted_at: Optional[datetime]
    rejected_at: Optional[datetime]
    change_date: Optional[datetime]
    # @Column(nullable = false)
    status: Status = Field(default=Status.NEGOTIATIONS_IN_PROGRESS, sa_column=Column(Enum(Status), nullable=False))
    # @Column(nullable = false)
    contract_no: str = Field(default=0, sa_column=Column(String, nullable=False))

    def __eq__(self, o):
        if not isinstance(o, Contract):
            return False
        return self.id is not None and self.id == o.id