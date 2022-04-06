from __future__ import annotations

import enum
from decimal import Decimal
from typing import Optional, Set

from common.base_entity import BaseEntity
from entity import Transit
from sqlalchemy import Column, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlmodel import Field, Relationship


class Driver(BaseEntity, table=True):
    __table_args__ = {'extend_existing': True}

    class Type(enum.Enum):
        CANDIDATE = 1
        REGULAR = 2

    class Status(enum.Enum):
        ACTIVE = 1
        INACTIVE = 2

    type: Optional[Type] = Field(sa_column=Column(Enum(Type)))
    status: Status = Field(sa_column=Column(Enum(Status)), nullable=False)

    first_name: Optional[str]
    last_name: Optional[str]
    photo: Optional[str]

    driver_license: str = Field(sa_column=Column(String, nullable=False))

    # @OneToOne
    fee: Optional[DriverFee] = Relationship(
        sa_relationship=relationship(
            "entity.driver_fee.DriverFee",
            back_populates="driver", uselist=False,)
    )

    is_occupied: Optional[bool]

    # @OneToMany(mappedBy = "driver")
    attributes: Set[DriverAttribute] = Relationship(
        sa_relationship=relationship(
            "entity.driver_attribute.DriverAttribute", back_populates="driver")
    )

    # @OneToMany(mappedBy = "driver")
    transits: Set[Transit] = Relationship(
        sa_relationship=relationship(
            "entity.transit.Transit", back_populates="driver")
    )

    def calculate_earnings_for_transit(self, transit: Transit) -> Optional[Decimal]:
        return None
        # zdublować kod wyliczenia kosztu przejazdu

    def __eq__(self, o):
        if not isinstance(o, Driver):
            return False
        return self.id is not None and self.id == o.id