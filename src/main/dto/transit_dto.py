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
        if transit is not None:
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
        self.set_tariff(transit)

    def set_tariff(self, transit: Transit) -> None:
        day = datetime.now()

        # wprowadzenie nowych cennikow od 1.01.2019
        if day.year <= 2018:
            self.km_rate = 1.0
            self.tariff = "Standard"
            return

        year = day.year
        leap = ((year % 4 == 0) and (year % 100 != 0)) or (year % 400 == 0)

        if (leap and day.timetuple().tm_yday == 366) or (not leap and day.timetuple().tm_yday == 365) or (day.timetuple().tm_yday == 1 and day.hour <= 6):
            self.tariff = "Sylwester"
            self.km_rate = 3.50
        else:
            match day.weekday():
                case 0 | 1 | 2 | 3:
                    self.km_rate = 1.0
                    self.tariff = "Standard"
                case 4:
                    if day.hour < 17:
                        self.km_rate = 1.0
                        self.tariff = "Standard"
                    else:
                        self.tariff = "Weekend+"
                        self.km_rate = 2.50
                case 5:
                    if day.hour < 6 or day.hour >= 17:
                        self.km_rate = 2.5
                        self.tariff = "Weekend+"
                    elif day.hour < 17:
                        self.km_rate = 1.5
                        self.tariff = "Weekend"
                case 6:
                    if day.hour < 6:
                        self.km_rate = 2.5
                        self.tariff = "Weekend+"
                    else:
                        self.km_rate = 1.5
                        self.tariff = "Weekend"

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