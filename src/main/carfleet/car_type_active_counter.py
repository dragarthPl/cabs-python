from typing import Any

from sqlalchemy import Column, Integer
from sqlmodel import SQLModel, Field

from carfleet.car_class import CarClass
from common.base_entity import EnumAsInteger


class CarTypeActiveCounter(SQLModel, table=True):
    __table_args__ = {'extend_existing': True}

    car_class: CarClass = Field(
        primary_key=True,
        sa_column=Column(EnumAsInteger(
            CarClass,
        ), nullable=False, primary_key=True)
    )

    active_cars_counter: int = Field(default=0, sa_column=Column(Integer, nullable=False))

    def __init__(self, car_class: CarClass, **data: Any):
        super().__init__(**data)
        self.car_class = car_class

    def __eq__(self, o):
        if not isinstance(o, CarTypeActiveCounter):
            return False
        return self.car_class is not None and self.car_class == o.car_class

