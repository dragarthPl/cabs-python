from __future__ import annotations

import enum
import hashlib
import uuid as uuid_pkg

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, Enum, LargeBinary
from sqlalchemy.orm import relationship
from sqlmodel import Field, Relationship

from common.base_entity import BaseEntity, new_uuid


class ContractAttachment(BaseEntity, table=True):
    __table_args__ = {'extend_existing': True}

    class Status(enum.Enum):
        PROPOSED = 1
        ACCEPTED_BY_ONE_SIDE = 2
        ACCEPTED_BY_BOTH_SIDES = 3
        REJECTED = 4

    contract_attachment_no: uuid_pkg.UUID = Field(
        default_factory=new_uuid,
        nullable=False,
    )

    accepted_at: Optional[datetime]
    rejected_at: Optional[datetime]
    change_date: Optional[datetime]
    status: Optional[Status] = Field(default=Status.PROPOSED, sa_column=Column(Enum(Status)))

    # @ManyToOne
    contract_id: Optional[int] = Field(default=None, foreign_key="contract.id")
    contract: Optional[Contract] = Relationship(
        sa_relationship=relationship(
            "entity.contract.Contract", back_populates="attachments"),
    )

    def __eq__(self, o):
        if not isinstance(o, ContractAttachment):
            return False
        return self.id is not None and self.id == o.id

    def __hash__(self):
        m = hashlib.md5()
        for s in (
                self.id,
                self.accepted_at,
                self.rejected_at,
                self.change_date,
                self.status,
        ):
            m.update(str(s).encode('utf-8'))
        return int(m.hexdigest(), 16)
