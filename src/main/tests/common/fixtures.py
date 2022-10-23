import inspect
from datetime import datetime
from typing import Any, Dict, Type, TypeVar

import fastapi
from fastapi.params import Depends
from injector import Injector, inject
from mypy.types import Instance
from sqlmodel import Session

from carfleet.car_class import CarClass
from carfleet.car_type_dto import CarTypeDTO
from common.application_event_publisher import ApplicationEventPublisher
from core.database import DatabaseModule
from dto.address_dto import AddressDTO
from dto.transit_dto import TransitDTO
from entity import Driver, Transit, DriverFee, Address, Client, CarType, Claim, DriverAttribute
from party.infra.party_relationship_repository_impl import PartyRelationshipRepositoryImpl
from party.infra.party_repository_impl import PartyRepositoryImpl
from party.model.party.party_relationship_repository import PartyRelationshipRepository
from party.model.party.party_repository import PartyRepository
from service.awards_service import AwardsService
from service.awards_service_impl import AwardsServiceImpl
from service.geocoding_service import GeocodingService
from tests.common.address_fixture import AddressFixture
from tests.common.awards_account_fixture import AwardsAccountFixture
from tests.common.car_type_fixture import CarTypeFixture
from tests.common.claim_fixture import ClaimFixture
from tests.common.client_fixture import ClientFixture
from tests.common.driver_fixture import DriverFixture
from tests.common.ride_fixture import RideFixture
from tests.common.transit_fixture import TransitFixture


T = TypeVar('T')


class DefaultFakeApplicationEventPublisher(ApplicationEventPublisher):

    def __init__(self):
        ...

    def publish_event_object(self, event: Any):
        ...


class DependencyResolver:
    injector: Injector
    dependency_cache: Dict[str, Any]
    abstract_map: Dict[str, Any]

    def __init__(self):
        def configure(binder):
            binder.bind(AwardsService, to=AwardsServiceImpl)
            binder.bind(PartyRepository, to=PartyRepositoryImpl)
            binder.bind(PartyRelationshipRepository, to=PartyRelationshipRepositoryImpl)
            binder.bind(ApplicationEventPublisher, to=DefaultFakeApplicationEventPublisher)

        self.injector = Injector([configure, DatabaseModule])

    def resolve_dependency(self, interface: Type[T]) -> T:
        return self.injector.get(interface)


class Fixtures:
    address_fixture: AddressFixture
    claim_fixture: ClaimFixture
    driver_fixture: DriverFixture
    client_fixture: ClientFixture
    transit_fixture: TransitFixture
    awards_account_fixture: AwardsAccountFixture
    car_type_fixture: CarTypeFixture
    ride_fixture: RideFixture

    @inject
    def __init__(
        self,
        address_fixture: AddressFixture,
        claim_fixture: ClaimFixture,
        driver_fixture: DriverFixture,
        client_fixture: ClientFixture,
        transit_fixture: TransitFixture,
        awards_account_fixture: AwardsAccountFixture,
        car_type_fixture: CarTypeFixture,
        ride_fixture: RideFixture,
    ):
        self.address_fixture = address_fixture
        self.claim_fixture = claim_fixture
        self.driver_fixture = driver_fixture
        self.client_fixture = client_fixture
        self.transit_fixture = transit_fixture
        self.awards_account_fixture = awards_account_fixture
        self.car_type_fixture = car_type_fixture
        self.ride_fixture = ride_fixture

    def an_address(self) -> Address:
        return self.address_fixture.an_address()

    def a_client(self) -> Client:
        return self.client_fixture.a_client_default()

    def a_client_with_type(self, client_type: Client.Type) -> Client:
        return self.client_fixture.a_client(client_type)

    def transit_details_client(self, driver: Driver, price: int, when: datetime, client: Client) -> Transit:
        return self.transit_fixture.transit_details(
            driver, price, when, client, self.an_address(), self.an_address())

    def transit_details(self, driver: Driver, price: int, when: datetime) -> Transit:
        return self.transit_fixture.transit_details(
            driver, price, when, self.a_client(), self.an_address(), self.an_address())

    def a_transit_dto(self, address_from: AddressDTO, address_to: AddressDTO) -> TransitDTO:
        return self.transit_fixture.a_transit_dto_for_client(self.a_client(), address_from, address_to)

    def driver_has_min_fee(self, driver: Driver, fee_type: DriverFee.FeeType, amount: int, min: int):
        return self.driver_fixture.driver_has_min_fee(driver, fee_type, amount, min)

    def driver_has_fee(self, driver: Driver, fee_type: DriverFee.FeeType, amount: int) -> DriverFee:
        return self.driver_fixture.driver_has_min_fee(driver, fee_type, amount, 0)

    def an_active_regular_driver(self) -> Driver:
        return self.driver_fixture.a_driver(
            Driver.Status.ACTIVE,
            "Janusz",
            "Kowalsi",
            "FARME100165AB5EW",
        )

    def a_driver(self, status: Driver.Status, name: str, last_name: str, driver_license: str) -> Driver:
        return self.driver_fixture.a_driver(
            status, name, last_name, driver_license
        )

    def a_random_nearby_driver(self, stubbed_geocoding_service: GeocodingService, pickup: Address) -> Driver:
        return self.driver_fixture.a_random_nearby_driver(stubbed_geocoding_service, pickup)

    def a_nearby_driver_default(
        self,
        plate_number: str,
        latitude: float,
        longitude: float,
        car_class: CarClass,
        when: datetime
    ) -> Driver:
        return self.driver_fixture.a_nearby_driver_default(plate_number, latitude, longitude, car_class, when)

    def a_nearby_driver(
            self,
            plate_number: str,
            latitude: float,
            longitude: float,
            car_class: CarClass,
            when: datetime,
            car_brand: str
    ) -> Driver:
        return self.driver_fixture.a_nearby_driver(plate_number, latitude, longitude, car_class, when, car_brand)

    def driver_has_attribute(self, driver: Driver, name: DriverAttribute.DriverAttributeName, value: str):
        self.driver_fixture.driver_has_attribute(driver, name, value)

    def a_journey(
            self, price: int, client: Client, driver: Driver, address_from: Address, destination: Address) -> Transit:
        return self.ride_fixture.a_ride(price, client, driver, address_from, destination)

    def a_journey_with_fixed_clock(
            self,
            price: int,
            published_at: datetime,
            completed_at: datetime,
            client: Client,
            driver: Driver,
            address_from: Address,
            destination: Address
    ) -> Transit:
        return self.ride_fixture.a_ride_with_fixed_clock(price, published_at, completed_at, client, driver, address_from, destination)

    def an_active_car_category(self, car_class: CarClass) -> CarTypeDTO:
        return self.car_type_fixture.an_active_car_category(car_class)

    def client_has_done_transits(self, client: Client, no_of_transits: int, geocoding_service: GeocodingService):
        for _ in range(1, no_of_transits + 1):
            pickup: Address = self.an_address()
            driver: Driver = self.a_random_nearby_driver(geocoding_service, pickup)
            self.a_journey(10, client, driver, pickup, self.an_address())

    def create_claim(self, client: Client, transit: Transit) -> Claim:
        return self.claim_fixture.create_claim_default_reason(client, transit)

    def create_claim_reason(self, client: Client, transit: Transit, reason: str) -> Claim:
        return self.claim_fixture.create_claim(client, transit, reason)

    def create_and_resolve_claim(self, client: Client, transit: Transit):
        return self.claim_fixture.create_and_resolve_claim(client, transit)

    def client_has_done_claim_after_completed_transit(self, client: Client, how_many: int) -> None:
        [
            self.create_and_resolve_claim(
                client, self.transit_details_client(
                    self.driver_fixture.an_active_regular_driver(), 20, datetime.now(), client)
            )
            for _ in range(1, how_many + 1)
        ]

    def a_client_with_claims(self, client_type: Client.Type, how_many_claims: int) -> Client:
        client = self.client_fixture.a_client(client_type)
        self.client_has_done_claim_after_completed_transit(client, how_many_claims)
        return client

    def active_awards_account(self, client: Client) -> None:
        self.awards_account_fixture.active_awards_account(client)
