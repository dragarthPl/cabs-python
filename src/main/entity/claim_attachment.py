from datetime import datetime

from sqlalchemy import Column, DateTime, Binary
from sqlmodel import Field

from src.main.common.base_entity import BaseEntity
from entity import Claim


class ClaimAttachment(BaseEntity, table=True):
    _claim: Claim = Field(foreign_key="claim.id")
    _creation_date: datetime = Field(sa_column=Column(DateTime, nullable=False))
    description: str
    _data: bytes = Field(sa_column=Column('data', Binary))
