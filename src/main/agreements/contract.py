from __future__ import annotations

import uuid as uuid_pkg

from datetime import datetime
from typing import Set, Optional, Any

from sqlalchemy import Column, DateTime, Enum, String
from sqlalchemy.orm import relationship
from sqlmodel import Field, Relationship

from agreements.contract_attachment_status import ContractAttachmentStatus
from agreements.contract_status import ContractStatus
from common.base_entity import BaseEntity
from entity import ContractAttachment


class Contract(BaseEntity, table=True):
    __table_args__ = {'extend_existing': True}

    # @OneToMany(mappedBy = "contract")
    attachments: Set[ContractAttachment] = Relationship(
        sa_relationship=relationship(
            "agreements.contract_attachment.ContractAttachment", back_populates="contract")
    )
    partner_name: Optional[str]
    subject: Optional[str]
    # @Column(nullable=false)
    creation_date: datetime = Field(default=datetime.now(), sa_column=Column(DateTime, nullable=False))
    accepted_at: Optional[datetime]
    rejected_at: Optional[datetime]
    change_date: Optional[datetime]
    # @Column(nullable = false)
    status: ContractStatus = Field(default=ContractStatus.NEGOTIATIONS_IN_PROGRESS, sa_column=Column(Enum(ContractStatus), nullable=False))
    # @Column(nullable = false)
    contract_no: str = Field(default=0, sa_column=Column(String, nullable=False))

    def __init__(self, *, partner_name: str, subject: str, contract_no: str, **data: Any):
        super().__init__(**data)
        self.partner_name = partner_name
        self.subject = subject
        self.contract_no = contract_no

    def get_attachment_ids(self):
        return list(
            map(
                lambda contract_attachment: contract_attachment.contract_attachment_no,
                self.attachments
            )
        )

    def propose_attachment(self):
        contract_attachment = ContractAttachment()
        contract_attachment.contract = self
        if contract_attachment not in self.attachments:
            self.attachments.append(contract_attachment)
        return contract_attachment

    def accept(self):
        if all(map(lambda x: x.status == ContractAttachmentStatus.ACCEPTED_BY_BOTH_SIDES, self.attachments)):
            self.status = ContractStatus.ACCEPTED
        else:
            raise AttributeError("Not all attachments accepted by both sides")

    def reject(self):
        self.status = ContractStatus.REJECTED

    def accept_attachment(self, contract_attachment_no: uuid_pkg.UUID):
        contract_attachment = self.find_attachment(contract_attachment_no)
        if contract_attachment.status == ContractAttachmentStatus.ACCEPTED_BY_ONE_SIDE or \
                contract_attachment.status == ContractAttachmentStatus.ACCEPTED_BY_BOTH_SIDES:
            contract_attachment.status = ContractAttachmentStatus.ACCEPTED_BY_BOTH_SIDES
        else:
            contract_attachment.status = ContractAttachmentStatus.ACCEPTED_BY_ONE_SIDE

    def reject_attachment(self, contract_attachment_no: uuid_pkg.UUID) -> None:
        contract_attachment = self.find_attachment(contract_attachment_no)
        contract_attachment.status = ContractAttachmentStatus.REJECTED

    def remove(self, contract_attachment_no: uuid_pkg.UUID):
        self.attachments = list(
            filter(
                lambda attachment: attachment.contract_attachment_no != contract_attachment_no,
                self.attachments
            )
        )

    def find_attachment(self, attachment_no: uuid_pkg.UUID) -> Optional[ContractAttachment]:
        for attachment in self.attachments:
            if attachment.contract_attachment_no.int == attachment_no.int:
                return attachment
        return None

    def __eq__(self, o):
        if not isinstance(o, Contract):
            return False
        return self.id is not None and self.id == o.id
