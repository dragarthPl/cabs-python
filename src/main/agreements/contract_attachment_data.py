import uuid as uuid_pkg
from datetime import datetime
from typing import Any

from sqlmodel import Field

from sqlalchemy import Column, DateTime, LargeBinary
from common.base_entity import BaseEntity


class ContractAttachmentData(BaseEntity, table=True):
    __table_args__ = {'extend_existing': True}

    contract_attachment_no: uuid_pkg.UUID = Field(
        nullable=False,
    )

    # @Lob
    # @Column(name = "data", columnDefinition="BLOB")
    data: bytes = Field(sa_column=Column('data', LargeBinary))

    # @Column(nullable = false)
    creation_date: datetime = Field(default=datetime.now(), sa_column=Column(DateTime, nullable=False))

    def __init__(self, *, contract_attachment_id: uuid_pkg.UUID, data: bytes, **kwargs: Any):
        super().__init__(**kwargs)
        self.contract_attachment_no = contract_attachment_id
        self.data = data

    def __eq__(self, o):
        if not isinstance(o, ContractAttachmentData):
            return False
        return self.id is not None and self.id == o.id

    def __hash__(self):
        return self.contract_attachment_no.int
