from __future__ import annotations


from datetime import datetime
from typing import Optional, Any

from sqlmodel import Field, Relationship
from sqlalchemy import Column, Integer, DateTime

from common.base_entity import BaseEntity
from loyalty.miles import Miles
from loyalty.miles_json_mapper import MilesJsonMapper


class AwardedMiles(BaseEntity, table=True):
    __table_args__ = {'extend_existing': True}

    client_id: Optional[int] = Field(default=0, sa_column=Column(Integer, nullable=True))

    # @Column(nullable = false)
    date: datetime = Field(default=datetime.now(), sa_column=Column(DateTime, nullable=False))

    miles_json: str = None

    transit_id: Optional[int] = Field(default=0, sa_column=Column(Integer, nullable=True))

    # @ManyToOne
    account_id: Optional[int] = Field(default=None, foreign_key="awardsaccount.id")
    account: AwardsAccount = Relationship(
        sa_relationship_kwargs=dict(foreign_keys="[AwardedMiles.account_id]")
    )

    def __init__(
            self,
            *,
            awards_account: AwardsAccount,
            transit_id: int,
            client_id: int,
            when: datetime,
            constant_until: Miles,
            **data: Any
    ):
        super().__init__(**data)
        self.account = awards_account
        self.transit_id = transit_id
        self.client_id = client_id
        self.date = when
        self.__set_miles(constant_until)

    def transfer_to(self, account: AwardsAccount):
        self.client_id = account.client_id
        self.account = account

    def get_miles(self) -> Miles:
        return MilesJsonMapper.deserialize(self.miles_json)

    def __set_miles(self, miles: Miles):
        self.miles_json = MilesJsonMapper.serialize(miles)

    def get_miles_amount(self, when: datetime) -> int:
        return self.get_miles().get_amount_for(when)

    def get_expiration_date(self) -> datetime:
        return self.get_miles().expires_at()

    def can_expire(self):
        return self.get_expiration_date() == datetime.max

    def remove_all(self, for_when: datetime):
        self.__set_miles(self.get_miles().subtract(self.get_miles_amount(for_when), for_when))

    def subtract(self, miles: int, for_when: datetime):
        self.__set_miles(self.get_miles().subtract(miles, for_when))

    def __eq__(self, o):
        if not isinstance(o, AwardedMiles):
            return False
        return self.id is not None and self.id == o.id
