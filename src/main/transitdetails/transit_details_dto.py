from datetime import datetime
from typing import Any

from carfleet.car_class import CarClass
from distance.distance import Distance
from dto.address_dto import AddressDTO
from dto.client_dto import ClientDTO
from entity import Transit
from money import Money
from transitdetails.transit_details import TransitDetails


class TransitDetailsDTO:

    transit_id: int

    date_time: datetime

    completed_at: datetime

    client: ClientDTO

    car_type: CarClass

    address_from: AddressDTO

    address_to: AddressDTO

    started: datetime

    accepted_at: datetime

    price: Money

    driver_fee: Money

    driver_id: int

    estimated_price: Money

    status: Transit.Status

    published_at: datetime

    distance: Distance

    base_fee: int

    km_rate: float

    tariff_name: str

    def __init__(self, transit_details: TransitDetails = None, **data: Any):
        if transit_details:
            self.transit_id = transit_details.transit_id
            self.date_time = transit_details.date_time
            self.completed_at = transit_details.complete_at
            self.client = ClientDTO(**transit_details.client.dict())
            self.car_type = transit_details.car_type
            self.address_from = AddressDTO(**transit_details.address_from.dict())
            self.address_to = AddressDTO(**transit_details.address_to.dict())
            self.started = transit_details.started
            self.accepted_at = transit_details.accepted_at
            self.driver_fee = transit_details.get_drivers_fee()
            self.price = transit_details.get_price()
            self.driver_id = transit_details.driver_id
            self.estimated_price = transit_details.get_estimated_price()
            self.status = transit_details.status
            self.published_at = transit_details.published_at
            self.distance = transit_details.get_distance()
            self.base_fee = transit_details.get_base_fee()
            self.km_rate = transit_details.get_km_rate()
            self.tariff_name = transit_details.tariff_name
        else:
            self.transit_id = data["transit_id"]
            self.date_time = data["date_time"]
            self.completed_at = data["completed_at"]
            self.client = data["client"]
            self.car_type = data["car_type"]
            self.address_from = data["address_from"]
            self.address_to = data["address_to"]
            self.started = data["started"]
            self.accepted_at = data["accepted_at"]
            self.distance = data["distance"]
            self.km_rate = data["tariff"].km_rate
            self.base_fee = data["tariff"].base_fee
            self.tariff_name = data["tariff"].name
