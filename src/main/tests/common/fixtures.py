import inspect
from datetime import datetime
from typing import Any, Dict

import pytz
import fastapi
from fastapi.params import Depends

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


class DependencyResolver:
    dependency_cache: Dict[str, Any]
    abstract_map: Dict[str, Any]

    def __init__(self, abstract_map: Dict[str, fastapi.Depends] = None):
        self.dependency_cache = {}
        self.abstract_map = abstract_map or {}

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
    driver_attribute_repository: DriverAttributeRepositoryImp

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
        driver_attribute_repository: DriverAttributeRepositoryImp = Depends(DriverAttributeRepositoryImp),
    ):
        self.transit_repository = transit_repository
        self.fee_repository = fee_repository
        self.driver_service = driver_service
        self.client_repository = client_repository
        self.address_repository = address_repository
        self.car_type_service = car_type_service
        self.claim_service = claim_service
        self.awards_service = awards_service
        self.driver_attribute_repository = driver_attribute_repository

    def a_client(self) -> Client:
        return self.client_repository.save(Client())

    def a_client_with_type(self, client_type: Client.Type) -> Client:
        client = self.a_client()
        client.type = client_type
        return self.client_repository.save(client)

    def a_transit_price(self, price: Money) -> Transit:
        return self.a_transit_now(
            self.an_acitve_regular_driver(),
            price.to_int()
        )

    def a_transit(self, driver: Driver, price: int, when: datetime, client: Client) -> Transit:
        transit: Transit = Transit(
            address_from=None,
            address_to=None,
            client=client,
            car_class=None,
            date_time=when.astimezone(pytz.UTC),
            distance=Distance.ZERO,
        )
        transit.set_price(Money(price))
        transit.propose_to(driver)
        transit.accept_by(driver, datetime.now())
        return self.transit_repository.save(transit)

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

    def an_acitve_regular_driver(self) -> Driver:
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

    def a_completed_transit_at(self, price: int, when: datetime):
        return self._a_completed_transit_at(price, when, self.a_client(), self.an_acitve_regular_driver())

    def _a_completed_transit_at(self, price: int, when: datetime, client: Client, driver: Driver):
        destination = self.address_repository.save(
            Address(country="Polska", city="Warszawa", street="Zytnia", building_number=20))
        transit = Transit(
            address_from=self.address_repository.save(
                Address(country="Polska", city="Warszawa", street="Młynarska", building_number=20)
            ),
            address_to=destination,
            client_id=client.id,
            car_class=None,
            date_time=when,
            distance=Distance.ZERO,
        )
        transit.publish_at(when)
        transit.propose_to(driver)
        transit.accept_by(driver, datetime.now())
        transit.start(datetime.now())
        transit.complete_ride_at(datetime.now(), destination, Distance.of_km(20))
        transit.set_price(Money(price))
        return self.transit_repository.save(transit)

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
                self._a_completed_transit_at(10, datetime.now(), client, self.an_acitve_regular_driver())
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
            self.create_and_resolve_claim(client, self.a_transit(self.an_acitve_regular_driver(), 20, datetime.now(), client))
            for _ in range(1, how_many + 1)
        ]

    def a_client_with_claims(self, client_type: Client.Type, how_many_claims: int) -> Client:
        client = self.a_client_with_type(client_type)
        self.client_has_done_claims(client, how_many_claims)
        return client

    def awards_account(self, client: Client) -> None:
        self.awards_service.register_to_program(client.id)

    def active_awards_account(self, client: Client) -> None:
        self.awards_account(client)
        self.awards_service.activate_account(client.id)

    def driver_has_attribute(self, driver: Driver, name: DriverAttribute.DriverAttributeName, value: str):
        self.driver_attribute_repository.save(DriverAttribute(driver=driver, name=name, value=value))
