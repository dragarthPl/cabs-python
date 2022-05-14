from __future__ import annotations

import enum
from datetime import datetime
from typing import Set, Optional, Any

from sqlalchemy import Column, DateTime, Enum, String
from sqlalchemy.orm import relationship
from sqlmodel import Field, Relationship

from common.base_entity import BaseEntity
from entity import ContractAttachment


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

    def __init__(self, *, partner_name: str, subject: str, contract_no: str, **data: Any):
        super().__init__(**data)
        self.partner_name = partner_name
        self.subject = subject
        self.contract_no = contract_no

    def propose_attachment(self, data: bytes):
        contract_attachment = ContractAttachment()
        contract_attachment.data = data
        contract_attachment.contract = self
        self.attachments.append(contract_attachment)
        return contract_attachment

    def accept(self):
        if all(map(lambda x: x.status == ContractAttachment.Status.ACCEPTED_BY_BOTH_SIDES, self.attachments)):
            self.status = Contract.Status.ACCEPTED
        else:
            raise AttributeError("Not all attachments accepted by both sides")

    def reject(self):
        self.status = Contract.Status.REJECTED

    def accept_attachment(self, attachment_id: int):
        contract_attachment = self.find_attachment(attachment_id)
        if contract_attachment.status == ContractAttachment.Status.ACCEPTED_BY_ONE_SIDE or \
                contract_attachment.status == ContractAttachment.Status.ACCEPTED_BY_BOTH_SIDES:
            contract_attachment.status = ContractAttachment.Status.ACCEPTED_BY_BOTH_SIDES
        else:
            contract_attachment.status = ContractAttachment.Status.ACCEPTED_BY_ONE_SIDE

    def reject_attachment(self, attachment_id: int) -> None:
        contract_attachment = self.find_attachment(attachment_id)
        contract_attachment.status = ContractAttachment.Status.REJECTED

    def find_attachment(self, attachment_id: int) -> Optional[ContractAttachment]:
        for attachment in self.attachments:
            if attachment.id == attachment_id:
                return attachment
        return None

    def __eq__(self, o):
        if not isinstance(o, Contract):
            return False
        return self.id is not None and self.id == o.id