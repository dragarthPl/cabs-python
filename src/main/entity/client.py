from __future__ import annotations
import enum
from typing import List
from sqlalchemy import Column, Enum
from sqlmodel import Field, Relationship

from entity.claim import Claim
from src.main.common.base_entity import BaseEntity

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

    a_type: Type = Field(sa_column=Column(Enum(Type)))
    name: str
    last_name: str

    default_payment_type: PaymentType = Field(sa_column=Column(Enum(PaymentType)))
    client_type: ClientType = Field(sa_column=Column(Enum(ClientType)))
    claims: List[Claim] = Relationship(back_populates="client")


__all__ = ["Client"]