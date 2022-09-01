import inspect
from datetime import datetime
from typing import Any, Dict

import pytz
import fastapi
from dateutil.relativedelta import relativedelta
from fastapi.params import Depends
from freezegun import freeze_time

from common.application_event_publisher import ApplicationEventPublisher
from distance.distance import Distance
from dto.address_dto import AddressDTO
from dto.car_type_dto import CarTypeDTO
from dto.claim_dto import ClaimDTO
from dto.client_dto import ClientDTO
from dto.transit_dto import TransitDTO
from entity import Driver, Transit, DriverFee, Address, Client, CarType, Claim, DriverAttribute
from money import Money
from repository.address_repository import AddressRepositoryImp
from repository.client_repository import ClientRepositoryImp
from repository.driver_attribute_repository import DriverAttributeRepositoryImp
from repository.driver_fee_repository import DriverFeeRepositoryImp
from repository.transit_repository import TransitRepositoryImp
from service.awards_service import AwardsService, AwardsServiceImpl
from service.car_type_service import CarTypeService
from service.claim_service import ClaimService
from service.driver_service import DriverService
from service.driver_session_service import DriverSessionService
from service.driver_tracking_service import DriverTrackingService
from service.geocoding_service import GeocodingService
from service.transit_service import TransitService
from tests.common.address_fixture import AddressFixture
from tests.common.awards_account_fixture import AwardsAccountFixture
from tests.common.car_type_fixture import CarTypeFixture
from tests.common.claim_fixture import ClaimFixture
from tests.common.client_fixture import ClientFixture
from tests.common.driver_fixture import DriverFixture
from tests.common.ride_fixture import RideFixture
from tests.common.transit_fixture import TransitFixture
from transitdetails.transit_details_facade import TransitDetailsFacade


class DefaultFakeApplicationEventPublisher(ApplicationEventPublisher):

    def __init__(self):
        ...

    def publish_event_object(self, event: Any):
        ...


class DependencyResolver:
    dependency_cache: Dict[str, Any]
    abstract_map: Dict[str, Any]

    def __init__(self, abstract_map: Dict[str, fastapi.Depends] = None):
        self.dependency_cache = {}
        self.abstract_map = abstract_map or {}
        self.abstract_map["Depends(ApplicationEventPublisher)"] = fastapi.Depends(DefaultFakeApplicationEventPublisher)

    def resolve_dependency(self, container: Any):
        container_key = str(container)
        if container_key in self.dependency_cache:
            return self.dependency_cache[container_key]
        if inspect.isabstract(container.dependency) and container_key in self.abstract_map:
            container = self.abstract_map[container_key]
        if isinstance(container, (Depends,)):
            new_container = container.dependency()
            if inspect.isgenerator(new_container):
                new_generator = next(new_container)
                self.dependency_cache[container_key] = new_generator
                return new_generator
            new_container = container.dependency
            prepare_kwargs = {}
            for name, parameter in inspect.signature(new_container.__init__).parameters.items():
                if parameter.default and isinstance(parameter.default, (Depends,)):
                    prepare_kwargs[name] = self.resolve_dependency(parameter.default)
            new_container_instance = new_container(**prepare_kwargs)
            self.dependency_cache[container_key] = new_container_instance
            return new_container_instance
        elif inspect.isclass(container) or callable(container):
            return self.resolve_dependency(container())
        elif inspect.isgenerator(container):
            new_generator = next(container)
            self.dependency_cache[container_key] = new_generator
            return next(new_generator)


class Fixtures:
    address_fixture: AddressFixture
    claim_fixture: ClaimFixture
    driver_fixture: DriverFixture
    client_fixture: ClientFixture
    transit_fixture: TransitFixture
    awards_account_fixture: AwardsAccountFixture
    car_type_fixture: CarTypeFixture
    ride_fixture: RideFixture

    def __init__(
        self,
        address_fixture: AddressFixture = Depends(AddressFixture),
        claim_fixture: ClaimFixture = Depends(ClaimFixture),
        driver_fixture: DriverFixture = Depends(DriverFixture),
        client_fixture: ClientFixture = Depends(ClientFixture),
        transit_fixture: TransitFixture = Depends(TransitFixture),
        awards_account_fixture: AwardsAccountFixture = Depends(AwardsAccountFixture),
        car_type_fixture: CarTypeFixture = Depends(CarTypeFixture),
        ride_fixture: RideFixture = Depends(RideFixture),
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

    def a_transit(self, driver: Driver, price: int, when: datetime, client: Client) -> Transit:
        return self.transit_fixture.a_transit(driver, price, when, client)

    def a_transit_price(self, price: Money) -> Transit:
        return self.transit_fixture.a_transit_when(
            self.driver_fixture.an_active_regular_driver(),
            price.to_int()
        )

    def a_transit_when(self, driver: Driver, price: int, when: datetime) -> Transit:
        return self.transit_fixture.a_transit(driver, price, when, None)

    def a_transit_now(self, driver: Driver, price: int) -> Transit:
        return self.transit_fixture.a_transit(driver, price, datetime.now(), None)

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
        car_class: CarType.CarClass,
        when: datetime
    ) -> Driver:
        return self.driver_fixture.a_nearby_driver_default(plate_number, latitude, longitude, car_class, when)

    def a_nearby_driver(
            self,
            plate_number: str,
            latitude: float,
            longitude: float,
            car_class: CarType.CarClass,
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

    def an_active_car_category(self, car_class: CarType.CarClass) -> CarType:
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
                client, self.a_transit(self.driver_fixture.an_active_regular_driver(), 20, datetime.now(), client))
            for _ in range(1, how_many + 1)
        ]

    def a_client_with_claims(self, client_type: Client.Type, how_many_claims: int) -> Client:
        client = self.client_fixture.a_client(client_type)
        self.client_has_done_claim_after_completed_transit(client, how_many_claims)
        return client

    def active_awards_account(self, client: Client) -> None:
        self.awards_account_fixture.active_awards_account(client)
