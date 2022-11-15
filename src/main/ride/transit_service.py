import math
from datetime import datetime
from typing import List, Set
from uuid import UUID

from injector import inject

from assignment.driver_assignment_facade import DriverAssignmentFacade
from assignment.involved_drivers_summary import InvolvedDriversSummary
from carfleet.car_class import CarClass
from common.application_event_publisher import ApplicationEventPublisher
from driverfleet.driver_dto import DriverDTO
from driverfleet.driver_service import DriverService
from geolocation.address.address import Address
from geolocation.distance import Distance
from geolocation.address.address_dto import AddressDTO
from pricing.tariff import Tariff
from pricing.tariffs import Tariffs
from ride import transit
from ride.details import transit_details
from ride.request_for_transit import RequestForTransit
from ride.request_for_transit_repository import RequestForTransitRepository
from ride.transit import Transit
from ride.transit_demand import TransitDemand
from ride.transit_demand_repository import TransitDemandRepository
from tracking.driver_position_dtov_2 import DriverPositionDTOV2
from ride.transit_dto import TransitDTO
from fastapi_events.dispatcher import dispatch

from ride.events.transit_completed import TransitCompleted
from money import Money
from geolocation.address.address_repository import AddressRepositoryImp
from crm.client_repository import ClientRepositoryImp
from tracking.driver_position_repository import DriverPositionRepositoryImp
from driverfleet.driver_repository import DriverRepositoryImp
from tracking.driver_session_repository import DriverSessionRepositoryImp
from ride.transit_repository import TransitRepositoryImp
from loyalty.awards_service import AwardsService
from carfleet.car_type_service import CarTypeService
from geolocation.distance_calculator import DistanceCalculator
from driverfleet.driver_fee_service import DriverFeeService
from crm.notification.driver_notification_service import DriverNotificationService
from geolocation.geocoding_service import GeocodingService
from invocing.invoice_generator import InvoiceGenerator
from tracking.driver_tracking_service import DriverTrackingService
from ride.details.transit_details_dto import TransitDetailsDTO
from ride.details.transit_details_facade import TransitDetailsFacade


#  If this class will still be here in 2022 I will quit.
class TransitService:
    driver_repository: DriverRepositoryImp
    transit_repository: TransitRepositoryImp
    client_repository: ClientRepositoryImp
    invoice_generator: InvoiceGenerator
    distance_calculator: DistanceCalculator
    geocoding_service: GeocodingService
    address_repository: AddressRepositoryImp
    driver_fee_service: DriverFeeService
    awards_service: AwardsService
    transit_details_facade: TransitDetailsFacade
    events_publisher: ApplicationEventPublisher
    driver_assignment_facade: DriverAssignmentFacade
    request_for_transit_repository: RequestForTransitRepository
    transit_demand_repository: TransitDemandRepository
    tariffs: Tariffs
    driver_service: DriverService

    @inject
    def __init__(
        self,
        driver_repository: DriverRepositoryImp,
        transit_repository: TransitRepositoryImp,
        client_repository: ClientRepositoryImp,
        invoice_generator: InvoiceGenerator,
        distance_calculator: DistanceCalculator,
        geocoding_service: GeocodingService,
        address_repository: AddressRepositoryImp,
        driver_fee_service: DriverFeeService,
        awards_service: AwardsService,
        transit_details_facade: TransitDetailsFacade,
        events_publisher: ApplicationEventPublisher,
        driver_assignment_facade: DriverAssignmentFacade,
        request_for_transit_repository: RequestForTransitRepository,
        transit_demand_repository: TransitDemandRepository,
        tariffs: Tariffs,
        driver_service: DriverService,
    ):
        self.driver_repository = driver_repository
        self.transit_repository = transit_repository
        self.client_repository = client_repository
        self.invoice_generator = invoice_generator
        self.distance_calculator = distance_calculator
        self.geocoding_service = geocoding_service
        self.address_repository = address_repository
        self.driver_fee_service = driver_fee_service
        self.awards_service = awards_service
        self.transit_details_facade = transit_details_facade
        self.events_publisher = events_publisher
        self.driver_assignment_facade = driver_assignment_facade
        self.request_for_transit_repository = request_for_transit_repository
        self.transit_demand_repository = transit_demand_repository
        self.tariffs = tariffs
        self.driver_service = driver_service

    def create_transit(self, transit_dto: TransitDTO) -> TransitDTO:
        address_from = self.__address_from_dto(transit_dto.address_from)
        address_to = self.__address_from_dto(transit_dto.address_to)
        return self.create_transit_transaction(
            transit_dto.client_dto.id, address_from, address_to, transit_dto.car_class)

    def __address_from_dto(self, address_dto: AddressDTO) -> Address:
        address = address_dto.to_address_entity()
        return self.address_repository.save(address)

    def create_transit_transaction(
            self, client_id: int, address_from: Address, address_to: Address, car_class: CarClass) -> TransitDTO:
        client = self.client_repository.get_one(client_id)
        if client is None:
            raise AttributeError("Client does not exist, id = " + str(client_id))

        # FIXME later: add some exceptions handling
        geo_from: List[float] = self.geocoding_service.geocode_address(address_from)
        geo_to: List[float] = self.geocoding_service.geocode_address(address_to)
        distance: Distance = Distance.of_km(float(self.distance_calculator.calculate_by_map(
            geo_from[0],
            geo_from[1],
            geo_to[0],
            geo_to[1]))
        )
        now: datetime = datetime.now()
        tariff: Tariff = self.choose_tariff(now)
        request_for_transit: RequestForTransit = self.request_for_transit_repository.save(
            RequestForTransit(tariff=tariff, distance=distance)
        )
        self.transit_details_facade.transit_requested(
            now,
            request_for_transit.request_uuid,
            address_from,
            address_to,
            distance,
            client,
            car_class,
            request_for_transit.get_estimated_price(),
            request_for_transit.get_tariff()
        )
        return self.load_transit_by_id(request_for_transit.id)

    def choose_tariff(self, when: datetime) -> Tariff:
        return self.tariffs.choose(when)

    def _change_transit_address_from(self, request_uuid: UUID, new_address: Address) -> None:
        new_address = self.address_repository.save(new_address)
        transit_demand: TransitDemand = self.transit_demand_repository.find_by_transit_request_uuid(request_uuid)
        if transit is None:
            raise AttributeError("Transit does not exist, id = " + str(request_uuid))
        if self.driver_assignment_facade.is_driver_assigned(request_uuid):
            raise AttributeError("Driver already assigned, requestUUID = " + str(request_uuid))
        transit_details: TransitDetailsDTO = self.transit_details_facade.find_by_uuid(request_uuid)

        # FIXME later: add some exceptions handling
        geo_from_new: List[float] = self.geocoding_service.geocode_address(new_address)
        geo_from_old: List[float] = self.geocoding_service.geocode_address(
            transit_details.address_from.to_address_entity()
        )

        # https://www.geeksforgeeks.org/program-distance-two-points-earth/
        # The math module contains a function
        # named toRadians which converts from
        # degrees to radians.
        lon1: float = math.radians(geo_from_new[1])
        lon2: float = math.radians(geo_from_old[1])
        lat1: float = math.radians(geo_from_new[0])
        lat2: float = math.radians(geo_from_old[0])

        # Haversine formula
        dlon: float = lon2 - lon1
        dlat: float = lat2 - lat1
        a: float = math.pow(math.sin(dlat / 2), 2) + math.cos(lat1) * math.cos(lat2) * math.pow(math.sin(dlon / 2), 2)

        c = 2 * math.asin(math.sqrt(a))

        # Radius of earth in kilometers. Use 3956 for miles
        r = 6371

        # calculate the result
        distance_in_kmeters = c * r

        new_distance = Distance.of_km(float(
            self.distance_calculator.calculate_by_map(
                geo_from_new[0],
                geo_from_new[1],
                geo_from_old[0],
                geo_from_old[1]
            )
        ))
        transit_demand.change_pickup(distance_in_kmeters)
        self.transit_details_facade.pickup_changed_to(request_uuid, new_address, new_distance)
        self.driver_assignment_facade.notify_proposed_drivers_about_changed_destination(request_uuid)

    def change_transit_address_to(self, request_uuid: UUID, new_address: AddressDTO) -> None:
        self._change_transit_address_to(request_uuid, new_address.to_address_entity())

    def change_transit_address_from(self, request_uuid: UUID, new_address: AddressDTO) -> None:
        self._change_transit_address_from(request_uuid, new_address.to_address_entity())

    def _change_transit_address_to(self, request_uuid: UUID, new_address: Address) -> None:
        self.address_repository.save(new_address)
        request_for_transit: RequestForTransit = self.request_for_transit_repository.find_by_request_uuid(request_uuid)
        transit_details: TransitDetailsDTO = self.transit_details_facade.find_by_uuid(request_uuid)
        if request_for_transit is None:
            raise AttributeError("Transit does not exist, id = " + str(request_uuid))

        # FIXME later: add some exceptions handling
        geo_from: List[float] = self.geocoding_service.geocode_address(transit_details.address_from.to_address_entity())
        geo_to: List[float] = self.geocoding_service.geocode_address(new_address)

        new_distance = Distance.of_km(float(
            self.distance_calculator.calculate_by_map(geo_from[0], geo_from[1], geo_to[0], geo_to[1])
        ))
        transit: Transit = self.transit_repository.find_by_transit_request_uuid(request_uuid)
        if transit:
            transit.change_destination(new_distance)
        self.driver_assignment_facade.notify_assigned_driver_about_changed_destination(request_uuid)
        self.transit_details_facade.destination_changed(request_uuid, new_address)

    def cancel_transit(self, request_uuid: UUID) -> None:
        transit: RequestForTransit = self.request_for_transit_repository.find_by_request_uuid(request_uuid)

        if transit is None:
            raise AttributeError("Transit does not exist, id = " + str(request_uuid))

        transit_demand: TransitDemand = self.transit_demand_repository.find_by_transit_request_uuid(request_uuid)
        if transit_demand is not None:
            transit_demand.cancel()
            self.driver_assignment_facade.cancel(request_uuid)

        self.transit_details_facade.transit_cancelled(request_uuid)

    def publish_transit(self, request_uuid: UUID) -> Transit:
        request_for: RequestForTransit = self.request_for_transit_repository.find_by_request_uuid(request_uuid)
        transit_details_dto: TransitDetailsDTO = self.transit_details_facade.find_by_uuid(request_uuid)

        if request_for is None:
            raise AttributeError("Transit does not exist, id = " + str(request_uuid))

        now: datetime = datetime.now()
        self.transit_demand_repository.save(TransitDemand(request_for.request_uuid))
        self.driver_assignment_facade.create_assignment(
            request_uuid,
            transit_details_dto.address_from,
            transit_details_dto.car_type,
            now
        )
        self.transit_details_facade.transit_published(request_uuid, now)
        return self.transit_repository.find_by_transit_request_uuid(request_uuid)

    def find_drivers_for_transit(self, request_uuid: UUID) -> Transit:
        transit_details_dto: TransitDetailsDTO = self.transit_details_facade.find_by_uuid(request_uuid)
        involved_drivers_summary: InvolvedDriversSummary = self.driver_assignment_facade.search_for_possible_drivers(
            request_uuid,
            transit_details_dto.address_from,
            transit_details_dto.car_type
        )
        self.transit_details_facade.drivers_are_involved(request_uuid, involved_drivers_summary)
        return self.transit_repository.find_by_transit_request_uuid(request_uuid)

    def accept_transit(self, driver_id: int, request_uuid: UUID):
        driver = self.driver_repository.get_one(driver_id)
        transit_demand: TransitDemand = self.transit_demand_repository.find_by_transit_request_uuid(request_uuid)

        if driver is None:
            raise AttributeError("Driver does not exist, id = " + str(driver_id))
        else:
            if self.driver_assignment_facade.is_driver_assigned(request_uuid):
                raise AttributeError(f"Driver already assigned, requestUUID = {request_uuid}")

            if transit_demand is None:
                raise AttributeError("Transit does not exist, id = " + str(request_uuid))
            else:
                now = datetime.now()
                transit_demand.accepted()
                self.driver_assignment_facade.accept_transit(request_uuid, driver)
                self.transit_details_facade.transit_accepted(request_uuid, driver_id, now)
                self.driver_repository.save(driver)

    def start_transit(self, driver_id: int, request_uuid: UUID):
        driver = self.driver_repository.get_one(driver_id)

        if driver is None:
            raise AttributeError("Driver does not exist, id = " + str(driver_id))

        transit_demand: TransitDemand = self.transit_demand_repository.find_by_transit_request_uuid(request_uuid)

        if transit_demand is None:
            raise AttributeError("Transit does not exist, id = " + str(request_uuid))
        if not self.driver_assignment_facade.is_driver_assigned(request_uuid):
            raise AttributeError("Driver not assigned, requestUUID = " + str(request_uuid))

        now = datetime.now()
        transit: Transit = Transit(tariff=self.choose_tariff(now), transit_request_uuid=request_uuid)
        self.transit_repository.save(transit)
        self.transit_details_facade.transit_started(request_uuid, transit.id, now)

    def reject_transit(self, driver_id: int, request_uuid: UUID):
        driver = self.driver_repository.get_one(driver_id)

        if driver is None:
            raise AttributeError("Driver does not exist, id = " + str(driver_id))

        self.driver_assignment_facade.reject_transit(request_uuid, driver_id)

    def complete_transit(self, driver_id: int, request_uuid: UUID, destination: AddressDTO):
        self._complete_transit(driver_id, request_uuid, destination.to_address_entity())

    def _complete_transit(self, driver_id: int, request_uuid: UUID, destination_address: Address):
        destination_address = self.address_repository.save(destination_address)
        driver = self.driver_repository.get_one(driver_id)
        transit_details: TransitDetailsDTO = self.transit_details_facade.find_by_uuid(request_uuid)

        if driver is None:
            raise AttributeError("Driver does not exist, id = " + str(driver_id))

        transit: Transit = self.transit_repository.find_by_transit_request_uuid(request_uuid)

        if transit is None:
            raise AttributeError("Transit does not exist, id = " + str(request_uuid))

        # FIXME later: add some exceptions handling
        geo_from: List[float] = self.geocoding_service.geocode_address(
            self.address_repository.get_by_hash(transit_details.address_from.hash))
        geo_to: List[float] = self.geocoding_service.geocode_address(
            self.address_repository.get_by_hash(transit_details.address_to.hash))
        distance = Distance.of_km(
            float(self.distance_calculator.calculate_by_map(geo_from[0], geo_from[1], geo_to[0], geo_to[1]))
        )
        now = datetime.now()
        final_price: Money = transit.complete_ride_at(distance)

        driver_fee: Money = self.driver_fee_service.calculate_driver_fee(final_price, driver_id)
        driver.is_occupied = False
        self.driver_repository.save(driver)
        self.awards_service.register_miles(transit_details.client.id, transit.id)
        self.transit_repository.save(transit)
        self.transit_details_facade.transit_completed(request_uuid, now, final_price, driver_fee)
        self.invoice_generator.generate(
            final_price.to_int(), f"{transit_details.client.name} {transit_details.client.last_name}")
        dispatch(
            "add_transit_between_addresses",
            payload=TransitCompleted(
                transit_details.client.id,
                transit.id,
                transit_details.address_from.hash,
                transit_details.address_to.hash,
                transit_details.started,
                now,
                datetime.now()
            ),
        )

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

    def get_request_uuid(self, request_uuid: int) -> UUID:
        return self.request_for_transit_repository.get_one(request_uuid).request_uuid
