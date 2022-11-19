import enum
from typing import Any
from uuid import UUID

from sqlalchemy import Column, Enum
from sqlmodel import Field

from common.base_entity import BaseEntity


class TransitDemand(BaseEntity, table=True):
    __table_args__ = {'extend_existing': True}

    transit_request_uuid: UUID

    class Status(enum.Enum):
        CANCELLED = 1
        WAITING_FOR_DRIVER_ASSIGNMENT = 2
        TRANSIT_TO_PASSENGER = 3

    status: Status = Field(sa_column=Column(Enum(Status)))
    pickup_address_change_counter: int = 0

    def __init__(self, transit_request_uuid: UUID, **data: Any):
        super().__init__(**data)
        self.transit_request_uuid = transit_request_uuid
        self.status = self.Status.WAITING_FOR_DRIVER_ASSIGNMENT

    def change_pickup(self, distance_from_previous_pickup: float):
        if distance_from_previous_pickup > 0.25:
            raise AttributeError(f"Address 'from' cannot be changed, id = {self.id}")
        elif self.status != self.Status.WAITING_FOR_DRIVER_ASSIGNMENT:
            raise AttributeError(f"Address 'from' cannot be changed, id = {self.id}")
        elif self.pickup_address_change_counter > 2:
            raise AttributeError(f"Address 'from' cannot be changed, id = {self.id}")
        self.pickup_address_change_counter = self.pickup_address_change_counter + 1

    def accept(self):
        self.status = self.Status.TRANSIT_TO_PASSENGER

    def cancel(self):
        if self.status != self.Status.WAITING_FOR_DRIVER_ASSIGNMENT:
            raise AttributeError(f"Demand cannot be cancelled, id =  {self.id}")
        self.status = self.Status.CANCELLED
