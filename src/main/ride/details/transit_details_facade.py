from datetime import datetime
from typing import Optional, List
from uuid import UUID

from injector import inject

from assignment.involved_drivers_summary import InvolvedDriversSummary
from carfleet.car_class import CarClass
from crm.client import Client
from geolocation.address.address import Address
from geolocation.distance import Distance
from money import Money
from pricing.tariff import Tariff
from ride.details.status import Status
from ride.details.transit_details import TransitDetails
from ride.details.transit_details_dto import TransitDetailsDTO
from ride.details.transit_details_repository import TransitDetailsRepository


class TransitDetailsFacade:
    transit_details_repository: TransitDetailsRepository

    @inject
    def __init__(
        self,
        transit_details_repository: TransitDetailsRepository,
    ):
        self.transit_details_repository = transit_details_repository

    def find_by_uuid(self, request_id: UUID) -> TransitDetailsDTO:
        return TransitDetailsDTO(self.load_by_uuid(request_id))

    def find(self, transit_id: int):
        return TransitDetailsDTO(transit_details=self.load(transit_id))

    def transit_requested(
        self,
        when: datetime,
        request_id: UUID,
        address_from: Optional[Address],
        address_to: Optional[Address],
        distance: Distance,
        client: Client,
        car_class: Optional[CarClass],
        estimated_price: Money,
        tariff: Tariff,
    ):
        transit_details: TransitDetails = TransitDetails(
            when=when,
            request_id=request_id,
            address_from=address_from,
            address_to=address_to,
            distance=distance,
            client=client,
            car_class=car_class,
            estimated_price=estimated_price,
            tariff=tariff,
        )
        self.transit_details_repository.save(transit_details)

    def pickup_changed_to(self, request_id: UUID, new_address: Address, new_distance: Distance):
        details: TransitDetails = self.load_by_uuid(request_id)
        details.pickup_changed_to(new_address, new_distance)

    def destination_changed(self, request_id: UUID, new_address: Address):
        details: TransitDetails = self.load_by_uuid(request_id)
        details.destination_changed_to(new_address)

    def transit_started(self, request_id: UUID, transit_id: int, when: datetime):
        details: TransitDetails = self.load_by_uuid(request_id)
        details.set_started_at(when, transit_id)

    def transit_accepted(self, request_id: UUID, driver_id: int, when: datetime):
        details: TransitDetails = self.load_by_uuid(request_id)
        details.set_accepted_at(when, driver_id)

    def transit_completed(self, request_id: UUID, when: datetime, price: Money, driver_fee: Money):
        details: TransitDetails = self.load_by_uuid(request_id)
        details.set_completed_at(when, price, driver_fee)
        self.transit_details_repository.save(details)

    def find_by_client(self, client_id: int) -> List[TransitDetailsDTO]:
        return list(map(
            lambda td: TransitDetailsDTO(td),
            self.transit_details_repository.find_by_client_id(client_id)
        ))

    def find_completed(self):
        return list(map(
            lambda x: TransitDetailsDTO(**x),
            self.transit_details_repository.find_by_status(Status.COMPLETED)
        ))

    def find_by_driver(self, driver_id: int, since: datetime, to: datetime) -> List[TransitDetailsDTO]:
        return list(map(
            lambda td: TransitDetailsDTO(td),
            self.transit_details_repository.find_all_by_driver_and_date_time_between(driver_id, since, to)
        ))

    def load_by_uuid(self, request_id: UUID):
        return self.transit_details_repository.find_by_request_uuid(request_id)

    def load(self, transit_id: int):
        return self.transit_details_repository.find_by_transit_id(transit_id)

    def transit_published(self, request_id: UUID, when: datetime):
        details: TransitDetails = self.load_by_uuid(request_id)
        details.set_published_at(when)

    def drivers_are_involved(self, request_id: UUID, involved_drivers_summary: InvolvedDriversSummary) -> None:
        details: TransitDetails = self.load_by_uuid(request_id)
        details.involved_drivers_are(involved_drivers_summary)

    def transit_cancelled(self, request_id: UUID):
        details: TransitDetails = self.load_by_uuid(request_id)
        details.cancelled()
