import enum
from typing import Optional

from carfleet.car_class import CarClass
from common.base_entity import BaseEntity
from sqlalchemy import Column, Enum, Integer
from sqlmodel import Field


class CarType(BaseEntity, table=True):
    __table_args__ = {'extend_existing': True}

    class Status(enum.IntEnum):
        INACTIVE = 1
        ACTIVE = 2

    #@Enumerated(EnumType.STRING)
    #@Column(nullable = false)
    car_class: CarClass = Field(sa_column=Column(Enum(CarClass), nullable=False))
    description: Optional[str]
    #@Enumerated(EnumType.STRING)
    status: Optional[Status] = Field(default=Status.INACTIVE, sa_column=Column(Enum(Status)))
    # @Column(nullable = false)
    cars_counter: int = Field(default=0, sa_column=Column(Integer, nullable=False))
    # @Column(nullable = false)
    min_no_of_cars_to_activate_class: int = Field(sa_column=Column(Integer, nullable=False))

    def register_car(self):
        self.cars_counter += 1

    def unregister_car(self):
        self.cars_counter += 1
        if self.cars_counter < 0:
            raise ValueError()

    def activate(self):
        if self.cars_counter < self.min_no_of_cars_to_activate_class:
            raise ValueError(f"Cannot activate car class when less than {self.min_no_of_cars_to_activate_class} cars in the fleet")
        self.status = self.Status.ACTIVE

    def deactivate(self):
        self.status = self.Status.INACTIVE

    def __eq__(self, o):
        if not isinstance(o, CarType):
            return False
        return self.id is not None and self.id == o.id

