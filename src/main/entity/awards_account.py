from datetime import datetime


from sqlalchemy import Column, DateTime, Boolean, Integer
from sqlalchemy.orm import relationship
from sqlmodel import Relationship, Field

from src.main.common.base_entity import BaseEntity
from entity import Client


class AwardsAccount(BaseEntity, table=True):

    #@OneToOne
    _client: Client = Relationship(sa_relationship=relationship("Client", back_populates="awards_account", uselist=False))
    #@Column(nullable = false)
    _date: datetime = Field(default=datetime.now(), sa_column=Column(DateTime, nullable=False))
    # @Column(nullable = false)
    _is_active: bool = Field(default=False, sa_column=Column(Boolean, nullable=False))
    #@Column(nullable = false)
    _transactions: int = Field(default=0, sa_column=Column(Integer, nullable=False))

    @property
    def client(self) -> Client:
        return self._client

    @client.setter
    def client(self, client: Client):
        self._client = client

    @property
    def date(self) -> datetime:
        return self.date

    @date.setter
    def date(self, date: datetime):
        self._date = date

    @property
    def is_active(self) -> bool:
        return self._is_active

    @property
    def transactions(self) -> int:
        return self._transactions

    def increase_transactions(self):
        self._transactions += 1

