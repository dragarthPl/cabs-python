import enum
from typing import Any, Optional

from deprecation import deprecated

from common.base_entity import BaseEntity
from sqlalchemy import Column, Enum, Integer
from sqlmodel import Field, SQLModel


class CarType(BaseEntity, table=True):
    __table_args__ = {'extend_existing': True}

    class Status(enum.IntEnum):
        INACTIVE = 1
        ACTIVE = 2

    class CarClass(enum.IntEnum):
        ECO = 1
        REGULAR = 2
        VAN = 3
        PREMIUM = 4

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

    active_cars_counter = Field(default=0, sa_column=Column(Integer, nullable=False))

    @deprecated(details="Deprecated")
    def register_active_car(self):
        self.active_cars_counter += 1

    @deprecated(details="Deprecated")
    def unregister_active_car(self):
        self.active_cars_counter -= 1

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

