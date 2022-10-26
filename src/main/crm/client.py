from __future__ import annotations

import enum
from typing import List, Optional

from sqlalchemy.orm import relationship

from crm.claims.claim import Claim
from sqlalchemy import Column, Enum
from sqlmodel import Field, Relationship

from common.base_entity import BaseEntity


class Client(BaseEntity, table=True):
    __table_args__ = {'extend_existing': True}

    class Type(enum.Enum):
        NORMAL = 1
        VIP = 2

    class ClientType(enum.Enum):
        INDIVIDUAL = 1
        COMPANY = 2

    class PaymentType(enum.Enum):
        PRE_PAID = 1
        POST_PAID = 2
        MONTHLY_INVOICE = 3

    type: Optional[Type] = Field(sa_column=Column(Enum(Type)))
    name: Optional[str]
    last_name: Optional[str]

    default_payment_type: Optional[PaymentType] = Field(sa_column=Column(Enum(PaymentType)))
    client_type: Optional[ClientType] = Field(sa_column=Column(Enum(ClientType)))

    def __eq__(self, o):
        if not isinstance(o, Client):
            return False
        return self.id is not None and self.id == o.id

__all__ = ["Client"]
