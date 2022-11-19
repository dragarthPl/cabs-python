import math
from datetime import datetime
from typing import List, Set
from uuid import UUID

from injector import inject

from assignment.driver_assignment_facade import DriverAssignmentFacade
from assignment.involved_drivers_summary import InvolvedDriversSummary
from carfleet.car_class import CarClass
from common.application_event_publisher import ApplicationEventPublisher
from crm.client import Client
from driverfleet.driver_dto import DriverDTO
from driverfleet.driver_service import DriverService
from geolocation.address.address import Address
from geolocation.distance import Distance
from geolocation.address.address_dto import AddressDTO
from pricing.tariff import Tariff
from pricing.tariffs import Tariffs
from ride import transit
from ride.change_destination_service import ChangeDestinationService
from ride.change_pickup_service import ChangePickupService
from ride.complete_transit_service import CompleteTransitService
from ride.demand_service import DemandService
from ride.request_for_transit import RequestForTransit
from ride.request_for_transit_repository import RequestForTransitRepository
from ride.request_transit_service import RequestTransitService
from ride.start_transit_service import StartTransitService
from ride.transit import Transit
from ride.transit_demand import TransitDemand
from ride.transit_demand_repository import TransitDemandRepository
from ride.transit_dto import TransitDTO
from fastapi_events.dispatcher import dispatch

from ride.events.transit_completed import TransitCompleted
from money import Money
from geolocation.address.address_repository import AddressRepositoryImp
from crm.client_repository import ClientRepositoryImp
from driverfleet.driver_repository import DriverRepositoryImp
from ride.transit_repository import TransitRepositoryImp
from loyalty.awards_service import AwardsService
from geolocation.distance_calculator import DistanceCalculator
from driverfleet.driver_fee_service import DriverFeeService
from geolocation.geocoding_service import GeocodingService
from invocing.invoice_generator import InvoiceGenerator
from ride.details.transit_details_dto import TransitDetailsDTO
from ride.details.transit_details_facade import TransitDetailsFacade


#  If this class will still be here in 2022 I will quit.
class RideService:
    request_transit_service: RequestTransitService
    change_pickup_service: ChangePickupService
    change_destination_service: ChangeDestinationService
    demand_service: DemandService
    complete_transit_service: CompleteTransitService
    start_transit_service: StartTransitService
    client_repository: ClientRepositoryImp
    invoice_generator: InvoiceGenerator
    address_repository: AddressRepositoryImp
    driver_fee_service: DriverFeeService
    awards_service: AwardsService
    transit_details_facade: TransitDetailsFacade
    events_publisher: ApplicationEventPublisher
    driver_assignment_facade: DriverAssignmentFacade
    driver_service: DriverService

    @inject
    def __init__(
        self,
        request_transit_service: RequestTransitService,
        change_pickup_service: ChangePickupService,
        change_destination_service: ChangeDestinationService,
        demand_service: DemandService,
        complete_transit_service: CompleteTransitService,
        start_transit_service: StartTransitService,
        transit_repository: TransitRepositoryImp,
        client_repository: ClientRepositoryImp,
        invoice_generator: InvoiceGenerator,
        address_repository: AddressRepositoryImp,
        driver_fee_service: DriverFeeService,
        awards_service: AwardsService,
        transit_details_facade: TransitDetailsFacade,
        events_publisher: ApplicationEventPublisher,
        driver_assignment_facade: DriverAssignmentFacade,
        driver_service: DriverService,
    ):
        self.request_transit_service = request_transit_service
        self.change_pickup_service = change_pickup_service
        self.change_destination_service = change_destination_service
        self.demand_service = demand_service
        self.complete_transit_service = complete_transit_service
        self.start_transit_service = start_transit_service
        self.transit_repository = transit_repository
        self.client_repository = client_repository
        self.invoice_generator = invoice_generator
        self.address_repository = address_repository
        self.driver_fee_service = driver_fee_service
        self.awards_service = awards_service
        self.transit_details_facade = transit_details_facade
        self.events_publisher = events_publisher
        self.driver_assignment_facade = driver_assignment_facade
        self.driver_service = driver_service

    def create_transit(self, transit_dto: TransitDTO) -> TransitDTO:
        return self.create_transit_transaction(
            transit_dto.client_dto.id,
            transit_dto.address_from,
            transit_dto.address_to,
            transit_dto.car_class
        )

    def create_transit_transaction(
            self, client_id: int, from_dto: AddressDTO, to_dto: AddressDTO, car_class: CarClass) -> TransitDTO:
        client = self.__find_client(client_id)
        address_from = self.__address_from_dto(from_dto)
        address_to = self.__address_from_dto(to_dto)
        now: datetime = datetime.now()
        request_for_transit: RequestForTransit = self.request_transit_service.create_request_for_transit(
            address_from,
            address_to,
        )
        self.transit_details_facade.transit_requested(
            now,
            request_for_transit.request_uuid,
            address_from,
            address_to,
            request_for_transit.get_distance(),
            client,
            car_class,
            request_for_transit.get_estimated_price(),
            request_for_transit.get_tariff()
        )
        return self.load_transit_by_id(request_for_transit.id)

    def __find_client(self, client_id: int) -> Client:
        client: Client = self.client_repository.get_one(client_id)
        if client is None:
            raise AttributeError(f"Client does not exist, id = {client_id}")
        return client

    def __address_from_dto(self, address_dto: AddressDTO) -> Address:
        address = address_dto.to_address_entity()
        return self.address_repository.save(address)

    def _change_transit_address_from(self, request_uuid: UUID, new_address: Address) -> None:
        if self.driver_assignment_facade.is_driver_assigned(request_uuid):
            raise AttributeError("Driver already assigned, requestUUID = " + str(request_uuid))
        new_address = self.address_repository.save(new_address)
        transit_details: TransitDetailsDTO = self.transit_details_facade.find_by_uuid(request_uuid)
        old_address: Address = transit_details.address_from.to_address_entity()
        new_distance: Distance = self.change_pickup_service.change_transit_address_from(
            request_uuid,
            new_address,
            old_address
        )
        self.transit_details_facade.pickup_changed_to(request_uuid, new_address, new_distance)
        self.driver_assignment_facade.notify_proposed_drivers_about_changed_destination(request_uuid)

    def change_transit_address_to(self, request_uuid: UUID, new_address: AddressDTO) -> None:
        self._change_transit_address_to(request_uuid, new_address.to_address_entity())

    def change_transit_address_from(self, request_uuid: UUID, new_address: AddressDTO) -> None:
        self._change_transit_address_from(request_uuid, new_address.to_address_entity())

    def _change_transit_address_to(self, request_uuid: UUID, new_address: Address) -> None:
        new_address = self.address_repository.save(new_address)
        transit_details: TransitDetailsDTO = self.transit_details_facade.find_by_uuid(request_uuid)
        if transit_details is None:
            raise AttributeError("Transit does not exist, id = " + str(request_uuid))
        old_address: Address = transit_details.address_from.to_address_entity()
        distance: Distance = self.change_destination_service.change_transit_address_to(
            request_uuid,
            new_address,
            old_address
        )

        self.driver_assignment_facade.notify_assigned_driver_about_changed_destination(request_uuid)
        self.transit_details_facade.destination_changed(request_uuid, new_address, distance)

    def cancel_transit(self, request_uuid: UUID) -> None:
        transit_details_dto: TransitDetailsDTO = self.transit_details_facade.find_by_uuid(request_uuid)
        if transit_details_dto is None:
            raise AttributeError(f"Transit does not exist, id = {request_uuid}")
        self.demand_service.cancel_demand(request_uuid)
        self.driver_assignment_facade.cancel(request_uuid)
        self.transit_details_facade.transit_cancelled(request_uuid)

    def publish_transit(self, request_uuid: UUID) -> None:
        transit_details_dto: TransitDetailsDTO = self.transit_details_facade.find_by_uuid(request_uuid)
        if transit_details_dto is None:
            raise AttributeError(f"Transit does not exist, id = {request_uuid}")
        self.demand_service.publish_demand(request_uuid)
        self.driver_assignment_facade.start_assigning_drivers(
            request_uuid,
            transit_details_dto.address_from,
            transit_details_dto.car_type,
            datetime.now()
        )
        self.transit_details_facade.transit_published(request_uuid, datetime.now())

    def find_drivers_for_transit(self, request_uuid: UUID) -> TransitDetailsDTO:
        transit_details_dto: TransitDetailsDTO = self.transit_details_facade.find_by_uuid(request_uuid)
        involved_drivers_summary: InvolvedDriversSummary = self.driver_assignment_facade.search_for_possible_drivers(
            request_uuid,
            transit_details_dto.address_from,
            transit_details_dto.car_type
        )
        self.transit_details_facade.drivers_are_involved(request_uuid, involved_drivers_summary)
        return self.transit_details_facade.find_by_uuid(request_uuid)

    def accept_transit(self, driver_id: int, request_uuid: UUID):
        if not self.driver_service.exists(driver_id) :
            raise AttributeError(f"Driver does not exist, id = {driver_id}")
        else:
            if self.driver_assignment_facade.is_driver_assigned(request_uuid):
                raise AttributeError(f"Driver already assigned, requestUUID = {request_uuid}")
            self.demand_service.accept_demand(request_uuid)
            self.driver_assignment_facade.accept_transit(request_uuid, driver_id)
            self.driver_service.mark_occupied(driver_id)
            self.transit_details_facade.transit_accepted(request_uuid, driver_id, datetime.now())

    def start_transit(self, driver_id: int, request_uuid: UUID):
        if not self.driver_service.exists(driver_id):
            raise AttributeError(f"Driver does not exist, id = {driver_id}")

        if not self.demand_service.exists_for(request_uuid):
            raise AttributeError(f"Transit does not exist, id = {request_uuid}")

        if not self.driver_assignment_facade.is_driver_assigned(request_uuid):
            raise AttributeError(f"Driver not assigned, requestUUID = {request_uuid}")

        now: datetime = datetime.now()
        transit: Transit = self.start_transit_service.start(request_uuid)
        self.transit_details_facade.transit_started(request_uuid, transit.id, now)

    def reject_transit(self, driver_id: int, request_uuid: UUID):
        if not self.driver_service.exists(driver_id):
            raise AttributeError(f"driver_does_not_exist, id = {driver_id}")
        self.driver_assignment_facade.reject_transit(request_uuid, driver_id)

    def complete_transit(self, driver_id: int, request_uuid: UUID, destination: AddressDTO):
        self._complete_transit(driver_id, request_uuid, destination.to_address_entity())

    def _complete_transit(self, driver_id: int, request_uuid: UUID, destination_address: Address):
        destination_address = self.address_repository.save(destination_address)
        transit_details: TransitDetailsDTO = self.transit_details_facade.find_by_uuid(request_uuid)
        if not self.driver_service.exists(driver_id):
            raise AttributeError(f"Driver does not exist, id = {driver_id}")

        address_from: Address = self.address_repository.get_by_hash(transit_details.address_from.hash)
        address_to: Address = self.address_repository.get_by_hash(destination_address.hash)
        final_price = self.complete_transit_service.complete_transit(
            driver_id,
            request_uuid,
            address_from,
            address_to
        )
        driver_fee: Money = self.driver_fee_service.calculate_driver_fee(final_price, driver_id)
        self.driver_service.mark_not_occupied(driver_id)
        self.transit_details_facade.transit_completed(request_uuid, datetime.now(), final_price, driver_fee)
        self.awards_service.register_miles(transit_details.client.id, transit_details.transit_id)
        self.invoice_generator.generate(
            final_price.to_int(),
            f"{transit_details.client.name} {transit_details.client.last_name}"
        )
        self.events_publisher.publish_event_object(TransitCompleted(
            transit_details.client.id,
            transit_details.transit_id,
            transit_details.address_from.hash,
            destination_address.hash,
            transit_details.started,
            datetime.now(),
            datetime.now()
        ))

    def load_transit_by_uuid(self, request_uuid: UUID) -> TransitDTO:
        involved_drivers_summary: InvolvedDriversSummary = self.driver_assignment_facade.load_involved_drivers_uuid(
            request_uuid
        )
        transit_details: TransitDetailsDTO = self.transit_details_facade.find_by_uuid(request_uuid)
        proposed_drivers: Set[DriverDTO] = self.driver_service.load_drivers(involved_drivers_summary.proposed_drivers)
        driver_rejections: Set[DriverDTO] = self.driver_service.load_drivers(involved_drivers_summary.driver_rejections)

        return TransitDTO(
            transit_details=transit_details,
            proposed_drivers=proposed_drivers,
            driver_rejections=driver_rejections,
            assigned_driver=involved_drivers_summary.assigned_driver
        )

    def load_transit_by_id(self, request_id: int) -> TransitDTO:
        request_uuid: UUID = self.get_request_uuid(request_id)
        return self.load_transit_by_uuid(request_uuid)

    def get_request_uuid(self, request_id: int) -> UUID:
        return self.request_transit_service.find_calculation_uuid(request_id)
