from datetime import datetime
from decimal import Decimal
from typing import Any, List, Optional, Set
from uuid import UUID

from carfleet.car_class import CarClass
from geolocation.distance import Distance
from geolocation.address.address_dto import AddressDTO
from crm.claims.claim_dto import ClaimDTO
from crm.client_dto import ClientDTO
from driverfleet.driver_dto import DriverDTO
from pydantic import BaseModel

from ride.details.status import Status
from ride.details.transit_details_dto import TransitDetailsDTO


class TransitDTO(BaseModel):
    id: Optional[int]
    request_id: Optional[UUID]
    tariff: Optional[str]
    status: Optional[Status]
    driver: Optional[DriverDTO]
    factor: Optional[int]
    distance: Optional[Distance]
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

    proposed_drivers: List[DriverDTO] = []
    address_to: Optional[AddressDTO]
    address_from: Optional[AddressDTO]
    car_class: Optional[CarClass]
    client_dto: Optional[ClientDTO]

    class Config:
        arbitrary_types_allowed = True

    def __init__(
        self,
        *,
        transit_details: TransitDetailsDTO = None,
        proposed_drivers: Set[DriverDTO] = None,
        driver_rejections: Set[DriverDTO] = None,
        assigned_driver: int = None,
        **data: Any,
    ):
        super().__init__(**data)
        self.factor = 1
        if assigned_driver and proposed_drivers:
            self.driver = next(filter(
                lambda driver: driver.id == assigned_driver,
                proposed_drivers
            ), None)
            self.proposed_drivers = list(proposed_drivers)

        if transit_details is not None:
            if hasattr(transit_details, "transit_id"):
                self.id = transit_details.transit_id
            if hasattr(transit_details, "request_uuid"):
                self.request_id = transit_details.request_uuid
            if hasattr(transit_details, "status"):
                self.status = transit_details.status
            if hasattr(transit_details, "price"):
                self.price = Decimal(transit_details.price.to_int() or 0)
            if hasattr(transit_details, "driver_fee"):
                self.driver_fee = Decimal(transit_details.driver_fee.to_int() or 0)
            if hasattr(transit_details, "estimated_price"):
                self.estimated_price = Decimal(transit_details.estimated_price.to_int() or 0)
            if transit_details.client:
                self.client_dto = ClientDTO(**transit_details.client.dict())
            if transit_details.address_from:
                self.address_from = AddressDTO(**transit_details.address_from.dict())
            if transit_details.address_to:
                self.address_to = AddressDTO(**transit_details.address_to.dict())
            if transit_details.date_time:
                self.date = transit_details.date_time
                self.date_time = transit_details.date_time
            if hasattr(transit_details, "published_at"):
                self.published = transit_details.published_at
            if transit_details.accepted_at:
                self.accepted_at = transit_details.accepted_at
            if transit_details.started:
                self.started = transit_details.started
            if transit_details.completed_at:
                self.complete_at = transit_details.completed_at
            if transit_details.car_type:
                self.car_class = transit_details.car_type
            if transit_details.distance:
                self.distance = transit_details.distance
            self.__set_tariff(transit_details)

    def __set_tariff(self, transit_details: TransitDetailsDTO) -> None:
        # wprowadzenie nowych cennikow od 1.01.2019
        self.tariff = transit_details.tariff_name
        self.km_rate = transit_details.km_rate
        self.base_fee = Decimal(transit_details.base_fee)

    def get_distance(self, unit: str) -> str:
        self.distance_unit = unit
        return self.distance.print_in(unit)
