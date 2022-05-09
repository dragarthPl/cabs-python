import json
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import relationship
from sqlmodel import Field, Relationship
from sqlalchemy import Column, Integer, DateTime

from common.base_entity import BaseEntity
from entity import Client, Miles
from entity import Transit
from entity import MilesJsonMapper


class AwardedMiles(BaseEntity, table=True):
    __table_args__ = {'extend_existing': True}

    # @ManyToOne
    client_id: Optional[int] = Field(default=None, foreign_key="client.id")
    client: Optional[Client] = Relationship(
        sa_relationship=relationship(
            "entity.client.Client")
    )

    # @Column(nullable = false)
    date: datetime = Field(default=datetime.now(), sa_column=Column(DateTime, nullable=False))

    miles_json: str = None

    # @ManyToOne
    transit_id: Optional[int] = Field(default=None, foreign_key="transit.id")
    transit: Optional[Transit] = Relationship(
        sa_relationship_kwargs=dict(foreign_keys="[AwardedMiles.transit_id]")
    )

    def get_miles(self) -> Miles:
        return MilesJsonMapper.deserialize(self.miles_json)

    def set_miles(self, miles: Miles):
        self.miles_json = MilesJsonMapper.serialize(miles)

    def get_miles_amount(self, when: datetime) -> int:
        return self.get_miles().get_amount_for(when)

    def get_expiration_date(self) -> datetime:
        return self.get_miles().expires_at()

    def can_expire(self):
        return self.get_expiration_date() == datetime.max

    def remove_all(self, for_when: datetime):
        self.set_miles(self.get_miles().subtract(self.get_miles_amount(for_when), for_when))

    def subtract(self, miles: int, for_when: datetime):
        self.set_miles(self.get_miles().subtract(miles, for_when))

    def __eq__(self, o):
        if not isinstance(o, AwardedMiles):
            return False
        return self.id is not None and self.id == o.id
