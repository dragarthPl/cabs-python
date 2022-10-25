from __future__ import annotations

import enum
from decimal import Decimal
from typing import Optional, Set, Any

from common.base_entity import BaseEntity
from entity import DriverLicense
from sqlalchemy import Column, Enum, String
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

    driver_license: str = Field(sa_column=Column(String))

    # @OneToOne
    fee: Optional[DriverFee] = Relationship(
        sa_relationship=relationship(
            "driverfleet.driver_fee.DriverFee",
            back_populates="driver", uselist=False,)
    )

    is_occupied: Optional[bool]

    # @OneToMany(mappedBy = "driver")
    attributes: Set[DriverAttribute] = Relationship(
        sa_relationship=relationship(
            "driverfleet.driver_attribute.DriverAttribute", back_populates="driver")
    )

    def __init__(self, **data: Any):
        super().__init__(**data)
        if "driver_license" in data:
            self.set_driver_license(data["driver_license"])

    def calculate_earnings_for_transit(self, transit: Transit) -> Optional[Decimal]:
        return None
        # zdublować kod wyliczenia kosztu przejazdu

    def get_driver_license(self) -> DriverLicense:
        return DriverLicense(driver_license=self.driver_license)

    def set_driver_license(self, driver_license: DriverLicense) -> None:
        self.driver_license = driver_license.as_string()

    def __eq__(self, o):
        if not isinstance(o, Driver):
            return False
        return self.id is not None and self.id == o.id