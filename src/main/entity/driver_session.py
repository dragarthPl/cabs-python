from datetime import datetime
from typing import Optional

from common.base_entity import BaseEntity
from entity.car_type import CarType
from entity.driver import Driver
from sqlalchemy import Column, DateTime, Enum, String
from sqlalchemy.orm import relationship
from sqlmodel import Field, Relationship


class DriverSession(BaseEntity, table=True):
    # @Column(nullable = false)
    logged_at: datetime = Field(sa_column=Column(DateTime, nullable=False))
    logged_out_at: Optional[datetime]
    # @ManyToOne
    driver_id: Optional[int] = Field(default=None, foreign_key="driver.id")
    driver: Optional[Driver] = Relationship(
        sa_relationship=relationship(
            "entity.driver.Driver")
    )
    # @Column(nullable = false)
    plates_number: str = Field(sa_column=Column(String, nullable=False))
    # @Enumerated(EnumType.STRING)
    car_class: Optional[CarType.CarClass] = Field(sa_column=Column(Enum(CarType.CarClass)))
    car_brand: Optional[str]

    def __eq__(self, o):
        if not isinstance(o, DriverSession):
            return False
        return self.id is not None and self.id == o.id
