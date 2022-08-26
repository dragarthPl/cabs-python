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
from service.transit_service import TransitService
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
    transit_repository: TransitRepositoryImp
    fee_repository: DriverFeeRepositoryImp
    driver_service: DriverService
    client_repository: ClientRepositoryImp
    address_repository: AddressRepositoryImp
    car_type_service: CarTypeService
    claim_service: ClaimService
    awards_service: AwardsServiceImpl
    transit_service: TransitService
    driver_attribute_repository: DriverAttributeRepositoryImp
    driver_session_service: DriverSessionService
    driver_tracking_service: DriverTrackingService
    transit_details_facade: TransitDetailsFacade

    def __init__(
        self,
        transit_repository: TransitRepositoryImp = Depends(TransitRepositoryImp),
        fee_repository: DriverFeeRepositoryImp = Depends(DriverFeeRepositoryImp),
        driver_service: DriverService = Depends(DriverService),
        client_repository: ClientRepositoryImp = Depends(ClientRepositoryImp),
        address_repository: AddressRepositoryImp = Depends(AddressRepositoryImp),
        car_type_service: CarTypeService = Depends(CarTypeService),
        claim_service: ClaimService = Depends(ClaimService),
        awards_service: AwardsServiceImpl = Depends(AwardsServiceImpl),
        transit_service: TransitService = Depends(TransitService),
        driver_attribute_repository: DriverAttributeRepositoryImp = Depends(DriverAttributeRepositoryImp),
        driver_session_service: DriverSessionService = Depends(DriverSessionService),
        driver_tracking_service: DriverTrackingService = Depends(DriverTrackingService),
        transit_details_facade: TransitDetailsFacade = Depends(TransitDetailsFacade),
    ):
        self.transit_repository = transit_repository
        self.fee_repository = fee_repository
        self.driver_service = driver_service
        self.client_repository = client_repository
        self.address_repository = address_repository
        self.car_type_service = car_type_service
        self.claim_service = claim_service
        self.awards_service = awards_service
        self.transit_service = transit_service
        self.driver_attribute_repository = driver_attribute_repository
        self.driver_session_service = driver_session_service
        self.driver_tracking_service = driver_tracking_service
        self.transit_details_facade = transit_details_facade

    def a_client(self) -> Client:
        return self.client_repository.save(Client())

    def a_client_with_type(self, client_type: Client.Type) -> Client:
        client = self.a_client()
        client.type = client_type
        return self.client_repository.save(client)

    def a_transit_price(self, price: Money) -> Transit:
        return self.a_transit_now(
            self.an_active_regular_driver(),
            price.to_int()
        )

    def a_transit(self, driver: Driver, price: int, when: datetime, client: Client) -> Transit:
        date_time = when.astimezone(pytz.UTC)
        transit: Transit = Transit(
            when=date_time,
            distance=Distance.ZERO,
        )
        transit.set_price(Money(price))
        transit.propose_to(driver)
        transit.accept_by(driver, datetime.now())
        transit = self.transit_repository.save(transit)
        self.transit_details_facade.transit_requested(
            when=date_time,
            transit_id=transit.id,
            address_from=None,
            address_to=None,
            distance=Distance.ZERO,
            client=client,
            car_class=None,
            estimated_price=Money(price),
            tariff=transit.get_tariff(),
        )
        return transit

    def a_transit_when(self, driver: Driver, price: int, when: datetime) -> Transit:
        self.a_transit(driver, price, when, None)

    def a_transit_now(self, driver: Driver, price: int) -> Transit:
        return self.a_transit(driver, price, datetime.now(), None)

    def driver_has_min_fee(self, driver: Driver, fee_type: DriverFee.FeeType, amount: int, min: int):
        driver_fee = DriverFee()
        driver_fee.driver = driver
        driver_fee.amount = amount
        driver_fee.fee_type = fee_type
        driver_fee.set_min(Money(min))
        return self.fee_repository.save(driver_fee)

    def driver_has_fee(self, driver: Driver, fee_type: DriverFee.FeeType, amount: int) -> DriverFee:
        return self.driver_has_min_fee(driver, fee_type, amount, 0)

    def an_active_regular_driver(self) -> Driver:
        return self.a_driver(
            Driver.Status.ACTIVE,
            "Janusz",
            "Kowalsi",
            "FARME100165AB5EW",
        )

    def a_driver(self, status: Driver.Status, name: str, last_name: str, driver_license: str) -> Driver:
        return self.driver_service.create_driver(
            driver_license,
            last_name,
            name,
            Driver.Type.REGULAR,
            status,
            "",
        )

    def a_nearby_driver(self, plate_number: str) -> Driver:
        driver: Driver = self.an_active_regular_driver()
        self.driver_has_fee(driver, DriverFee.FeeType.FLAT, 10)
        self.driver_session_service.log_in(driver.id, plate_number, CarType.CarClass.VAN, "BRAND")
        self.driver_tracking_service.register_position(driver.id, 1, 1, datetime.now())
        return driver

    def a_completed_transit_at_default(self, price: int, when: datetime):
        return self.a_completed_transit_at(price, when, self.a_client(), self.an_active_regular_driver())

    def a_requested_and_completed_transit(
            self,
            price: int,
            published_at: datetime,
            completed_at: datetime,
            client: Client,
            driver: Driver,
            address_from: Address,
            destination: Address
    ) -> Transit:
        address_from = self.address_repository.save(address_from)
        destination = self.address_repository.save(destination)
        transit: Transit = Transit(
            when=published_at,
            distance=Distance.ZERO
        )
        transit.publish_at(published_at)
        transit.propose_to(driver)
        transit.accept_by(driver, published_at)
        transit.start(published_at)
        transit.complete_ride_at(completed_at, destination, Distance.of_km(1))
        transit.set_price(Money(price))
        transit = self.transit_repository.save(transit)
        self.transit_details_facade.transit_requested(
            published_at,
            transit.id,
            address_from,
            destination,
            Distance.ZERO,
            client,
            None,
            Money(price),
            transit.get_tariff()
        )
        self.transit_details_facade.transit_accepted(transit.id, published_at, driver.id)
        self.transit_details_facade.transit_started(transit.id, published_at)
        self.transit_details_facade.transit_completed(
            transit.id,
            published_at,
            Money(price),
            Money(0)
        )
        return transit

    def _a_completed_transit_at(
            self,
            price: int,
            published_at: datetime,
            completed_at: datetime,
            client: Client,
            driver: Driver
    ):
        address_destination = self.address_repository.save(
            Address(country="Polska", city="Warszawa", street="Zytnia", building_number=20))
        address_from = self.address_repository.save(
            Address(country="Polska", city="Warszawa", street="Młynarska", building_number=20)
        )

        return self.a_requested_and_completed_transit(
            price, published_at, completed_at, client, driver, address_from, address_destination)

    def a_completed_transit_at(self, price: int, published_at: datetime, client: Client, driver: Driver):
        return self._a_completed_transit_at(
            price,
            published_at,
            published_at + relativedelta(minutes=10),
            client,
            driver
        )

    def _a_requested_and_completed_transit(
        self,
        price: int,
        published_at: datetime,
        completed_at: datetime,
        client: Client,
        driver: Driver,
        address_from: Address,
        address_destination: Address,
    ):
        address_from = self.address_repository.save(address_from)
        address_destination = self.address_repository.save(address_destination)

        with freeze_time(published_at):
            transit: Transit = self.transit_service.create_transit_transaction(
                client.id,
                address_from,
                address_destination,
                CarType.CarClass.VAN
            )
            self.transit_service.publish_transit(transit.id)
            self.transit_service.find_drivers_for_transit(transit.id)
            self.transit_service.accept_transit(driver.id, transit.id)
            self.transit_service.start_transit(driver.id, transit.id)

        with freeze_time(completed_at):
            self.transit_service._complete_transit(driver.id, transit.id, address_destination)

            return self.transit_repository.get_one(transit.id)

    def an_active_car_category(self, car_class: CarType.CarClass) -> CarType:
        car_type_dto = CarTypeDTO()
        car_type_dto.car_class = car_class
        car_type_dto.description = "opis"
        car_type = self.car_type_service.create(car_type_dto)
        [
            self.car_type_service.register_car(car_type.car_class)
            for _ in range(1, car_type.min_no_of_cars_to_activate_class + 1)
        ]
        self.car_type_service.activate(car_type.id)
        return car_type

    def a_transit_dto_for_client(self, client: Client, address_from: AddressDTO, address_to: AddressDTO):
        transit_dto = TransitDTO()
        transit_dto.client_dto = ClientDTO(**client.dict())
        transit_dto.address_from = address_from
        transit_dto.address_to = address_to
        return transit_dto

    def a_transit_dto(self, address_from: AddressDTO, address_to: AddressDTO) -> TransitDTO:
        return self.a_transit_dto_for_client(self.a_client(), address_from, address_to)

    def client_has_done_transits(self, client: Client, no_of_transits: int):
        for _ in range(1, no_of_transits + 1):
           self.transit_repository.save(
                self.a_completed_transit_at(10, datetime.now(), client, self.an_active_regular_driver())
           )

    def create_claim(self, client: Client, transit: Transit) -> Claim:
        claim_dto = self.claim_dto("Okradli mnie na hajs", "$$$", client.id, transit.id)
        claim_dto.is_draft = False
        claim = self.claim_service.create(claim_dto)
        return claim

    def create_claim_reason(self, client: Client, transit: Transit, reason: str) -> Claim:
        claim_dto = self.claim_dto("Okradli mnie na hajs", reason, client.id, transit.id)
        claim_dto.is_draft = False
        claim = self.claim_service.create(claim_dto)
        return claim

    def create_and_resolve_claim(self, client: Client, transit: Transit):
        claim = self.create_claim(client, transit)
        claim = self.claim_service.try_to_automatically_resolve(claim.id)
        return claim

    def claim_dto(self, desc: str, reason: str, client_id: int, transit_id: int) -> ClaimDTO:
        claim_dto = ClaimDTO()
        claim_dto.client_id = client_id
        claim_dto.transit_id = transit_id
        claim_dto.incident_description = desc
        claim_dto.reason = reason
        return claim_dto

    def client_has_done_claims(self, client: Client, how_many: int) -> None:
        [
            self.create_and_resolve_claim(client, self.a_transit(self.an_active_regular_driver(), 20, datetime.now(), client))
            for _ in range(1, how_many + 1)
        ]

    def awards_account(self, client: Client) -> None:
        self.awards_service.register_to_program(client.id)

    def a_client_with_claims(self, client_type: Client.Type, how_many_claims: int) -> Client:
        client = self.a_client_with_type(client_type)
        self.client_has_done_claims(client, how_many_claims)
        return client

    def active_awards_account(self, client: Client) -> None:
        self.awards_account(client)
        self.awards_service.activate_account(client.id)

    def driver_has_attribute(self, driver: Driver, name: DriverAttribute.DriverAttributeName, value: str):
        self.driver_attribute_repository.save(DriverAttribute(driver=driver, name=name, value=value))
