from datetime import datetime
from typing import Optional

from entity import Client
from sqlalchemy import Boolean, Column, DateTime, Integer
from sqlalchemy.orm import relationship, backref
from sqlmodel import Field, Relationship

from common.base_entity import BaseEntity


class AwardsAccount(BaseEntity, table=True):
    __table_args__ = {'extend_existing': True}

    # @OneToOne
    client_id: Optional[int] = Field(default=None, foreign_key="client.id")
    client: Optional[Client] = Relationship(sa_relationship=relationship("Client", backref=backref("awards_account", uselist=False)))
    #@Column(nullable = false)
    date: datetime = Field(default=datetime.now(), sa_column=Column(DateTime, nullable=False))
    # @Column(nullable = false)
    is_active: bool = Field(default=False, sa_column=Column(Boolean, nullable=False))
    #@Column(nullable = false)
    transactions: int = Field(default=0, sa_column=Column(Integer, nullable=False))

    def increase_transactions(self):
        self.transactions += 1

    def __eq__(self, o):
        if not isinstance(o, AwardsAccount):
            return False
        return self.id is not None and self.id == o.id
