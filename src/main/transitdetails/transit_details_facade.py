from datetime import datetime
from typing import Optional

from fastapi import Depends

from distance.distance import Distance
from entity import Address, Client, CarType, Tariff
from money import Money
from transitdetails.transit_details import TransitDetails
from transitdetails.transit_details_dto import TransitDetailsDTO
from transitdetails.transit_details_repository import TransitDetailsRepository


class TransitDetailsFacade:
    transit_details_repository: TransitDetailsRepository

    def __init__(
        self,
        transit_details_repository: TransitDetailsRepository = Depends(TransitDetailsRepository),
    ):
        self.transit_details_repository = transit_details_repository

    def find(self, transit_id: int):
        return TransitDetailsDTO(transit_details=self.load(transit_id))

    def transit_requested(
        self,
        when: datetime,
        transit_id: int,
        address_from: Optional[Address],
        address_to: Optional[Address],
        distance: Distance,
        client: Client,
        car_class: Optional[CarType.CarClass],
        estimated_price: Money,
        tariff: Tariff,
    ):
        transit_details: TransitDetails = TransitDetails(
            when=when,
            transit_id=transit_id,
            address_from=address_from,
            address_to=address_to,
            distance=distance,
            client=client,
            car_class=car_class,
            estimated_price=estimated_price,
            tariff=tariff,
        )
        self.transit_details_repository.save(transit_details)

    def pickup_changed_to(self, transit_id: int, new_address: Address, new_distance: Distance):
        details: TransitDetails = self.load(transit_id)
        details.pickup_changed_to(new_address, new_distance)

    def destination_changed(self, transit_id: int, new_address: Address, new_distance: Distance):
        details: TransitDetails = self.load(transit_id)
        details.destination_changed_to(new_address, new_distance)

    def transit_published(self, transit_id: int, when: datetime):
        details: TransitDetails = self.load(transit_id)
        details.set_published_at(when)

    def transit_started(self, transit_id: int, when: datetime):
        details: TransitDetails = self.load(transit_id)
        details.set_started_at(when)

    def transit_accepted(self, transit_id: int, when: datetime, driver_id: int):
        details: TransitDetails = self.load(transit_id)
        details.set_accepted_at(when, driver_id)

    def transit_cancelled(self, transit_id: int):
        details: TransitDetails = self.load(transit_id)
        details.cancelled()

    def transit_completed(self, transit_id: int, when: datetime, price: Money, driver_fee: Money):
        details: TransitDetails = self.load(transit_id)
        details.set_completed_at(when, price, driver_fee)
        self.transit_details_repository.save(details)

    def load(self, transit_id: int):
        return self.transit_details_repository.find_by_transit_id(transit_id)