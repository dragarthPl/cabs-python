from __future__ import annotations

import hashlib
import uuid as uuid_pkg

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, Enum
from sqlalchemy.orm import relationship
from sqlmodel import Field, Relationship

from agreements.contract_attachment_status import ContractAttachmentStatus
from common.base_entity import BaseEntity, new_uuid


class ContractAttachment(BaseEntity, table=True):
    __table_args__ = {'extend_existing': True}

    contract_attachment_no: uuid_pkg.UUID = Field(
        default_factory=new_uuid,
        nullable=False,
    )

    accepted_at: Optional[datetime]
    rejected_at: Optional[datetime]
    change_date: Optional[datetime]
    status: Optional[ContractAttachmentStatus] = Field(default=ContractAttachmentStatus.PROPOSED, sa_column=Column(Enum(ContractAttachmentStatus)))

    # @ManyToOne
    contract_id: Optional[int] = Field(default=None, foreign_key="contract.id")
    contract: Optional[Contract] = Relationship(
        sa_relationship=relationship(
            "agreements.contract.Contract", back_populates="attachments"),
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
