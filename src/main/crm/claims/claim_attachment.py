from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, LargeBinary
from sqlmodel import Field

from common.base_entity import BaseEntity
from crm.claims.claim import Claim


class ClaimAttachment(BaseEntity, table=True):
    # @ManyToOne
    claim: Optional[Claim] = Field(foreign_key="claim.id")
    # @Column(nullable = false)
    creation_date: datetime = Field(sa_column=Column(DateTime, nullable=False))
    description: Optional[str]

    # @Lob
    # @Column(name = "data", columnDefinition="BLOB")
    data: Optional[bytes] = Field(sa_column=Column('data', LargeBinary))

    def __eq__(self, o):
        if not isinstance(o, ClaimAttachment):
            return False
        return self.id is not None and self.id == o.id
