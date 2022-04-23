import math
from datetime import datetime
from decimal import Decimal
from typing import Any, List, Optional

from dto.address_dto import AddressDTO
from dto.claim_dto import ClaimDTO
from dto.client_dto import ClientDTO
from dto.driver_dto import DriverDTO
from entity import CarType, Transit
from pydantic import BaseModel


class TransitDTO(BaseModel):
    id: Optional[int]
    tariff: Optional[str]
    status: Optional[Transit.Status]
    driver: Optional[DriverDTO]
    factor: Optional[int]
    distance: Optional[float]
    distance_unit: Optional[str]
    km_rate: Optional[float]
    price: Optional[Decimal]
    driver_fee: Optional[Decimal]
    estimated_price: Optional[Decimal]
    base_fee: Optional[Decimal]
    date: Optional[datetime]
    date_time: Optional[datetime]
    published: Optional[datetime]
    accepted_at: Optional[datetime]
    started: Optional[datetime]
    complete_at: Optional[datetime]
    claim_dto: Optional[ClaimDTO]

    #new ArrayList<>();
    proposed_drivers: List[DriverDTO] = []
    address_to: Optional[AddressDTO]
    address_from: Optional[AddressDTO]
    car_class: Optional[CarType.CarClass]
    client_dto: Optional[ClientDTO]

    def __init__(self, *, transit: Transit = None, **data: Any):
        if transit is not None:
            data.update(**transit.dict())
        super().__init__(**data)
        self.factor = 1
        if transit is not None:
            if transit.get_price():
                self.price = Decimal(transit.get_price().to_int() or 0)
            if transit.get_drivers_fee():
                self.driver_fee = Decimal(transit.get_drivers_fee().to_int() or 0)
            if transit.get_estimated_price():
                self.estimated_price = Decimal(transit.get_estimated_price().to_int() or 0)

            if transit.address_from:
                self.address_from = AddressDTO(**transit.address_from.dict())
            if transit.address_to:
                self.address_to = AddressDTO(**transit.address_to.dict())
            if transit.client:
                self.client_dto = ClientDTO(**transit.client.dict())
            if transit.proposed_drivers:
                self.proposed_drivers = []
                for driver in transit.proposed_drivers:
                    self.proposed_drivers.append(DriverDTO(**driver.dict()))
            if transit.date_time:
                self.date = transit.date_time
            self.distance = transit.km
        self.set_tariff(transit)

    def set_tariff(self, transit: Transit) -> None:
        # wprowadzenie nowych cennikow od 1.01.2019
        self.tariff = transit.get_tariff().name
        self.km_rate = transit.get_tariff().km_rate
        self.base_fee = Decimal(transit.get_tariff().base_fee)

    def get_distance(self, unit: str) -> str:
        self.distance_unit = unit
        if unit == 'km':
            if self.distance == math.ceil(self.distance):
                return "%dkm" % round(self.distance)
            return "%.3fkm" % self.distance
        if unit == 'miles':
            distance = self.distance /1.609344
            if distance == math.ceil(distance):
                return "%dmiles" % round(distance)
            return "%.3fmiles" % distance

        if unit == 'm':
            return "%dm" % round(self.distance * 1000)
        raise AttributeError("Invalid unit " + unit)
