from __future__ import annotations

import enum
from datetime import datetime
from typing import Optional, Any
from uuid import UUID

from sqlalchemy.orm import composite

from common.base_entity import BaseEntity, new_uuid
from geolocation.distance import Distance
from sqlalchemy import Column, Enum, Float
from sqlmodel import Field

from money import Money
from pricing.tariff import Tariff

class Transit(BaseEntity, table=True):
    __table_args__ = {'extend_existing': True}

    class Status(enum.Enum):
        IN_TRANSIT = 1
        COMPLETED = 2

    transit_request_uuid: UUID = Field(
        default_factory=new_uuid,
        nullable=False,
    )
    status: Optional[Status] = Field(sa_column=Column(Enum(Status)))

    tariff_km_rate: Optional[float] = 0
    tariff_name: Optional[str] = None
    tariff_base_fee: Optional[int] = 0
    __tariff: Tariff = composite(Tariff, 'tariff_km_rate', 'tariff_name', 'tariff_base_fee')

    km: Optional[float] = Field(default=0.0, sa_column=Column(Float))

    def __init__(self, **data: Any):
        tariff: Optional[Tariff] = None
        km: Optional[Distance] = None
        status: Optional[Status] = self.Status.IN_TRANSIT
        when: Optional[datetime] = None
        if "tariff" in data:
            tariff = data.pop("tariff")
        if "km" in data:
            km = data.pop("km")
        if "status" in data:
            status = data.pop("status")
        super().__init__(**data)
        self.status = status
        if tariff:
            self.tariff_name = tariff.name
            self.tariff_base_fee = tariff.base_fee
            self.tariff_km_rate = tariff.km_rate
        if km:
            self.km = km.to_km_in_float()

    def change_destination(self, new_distance: Distance) -> None:
        if self.status == self.Status.COMPLETED:
            raise AttributeError("Address 'to' cannot be changed, id = " + str(self.id))

        self.km = new_distance.to_km_in_float()

    def complete_ride_at(self, distance: Distance) -> Money:
        if self.status == self.Status.IN_TRANSIT:
            self.km = distance.to_km_in_float()
            self.status = self.Status.COMPLETED
            return self.calculate_final_costs()
        else:
            raise AttributeError("Cannot complete Transit, id = " + str(self.id))

    def calculate_final_costs(self) -> Money:
        if self.status == self.Status.COMPLETED:
            return self.__calculate_cost()
        else:
            raise ValueError("Cannot calculate final cost if the transit is not completed")

    def __calculate_cost(self) -> Money:
        return self.get_tariff().calculate_cost(Distance.of_km(self.km))

    def get_distance(self) -> Distance:
        return Distance.of_km(self.km)

    def get_tariff(self):
        return self.__tariff

    def __eq__(self, o):
        if not isinstance(o, Transit):
            return False
        return self.id is not None and self.id == o.id
