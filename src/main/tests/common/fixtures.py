import inspect
from datetime import datetime
from typing import Any, Dict

import pytz
from fastapi.params import Depends

from distance.distance import Distance
from dto.address_dto import AddressDTO
from dto.car_type_dto import CarTypeDTO
from dto.client_dto import ClientDTO
from dto.transit_dto import TransitDTO
from entity import Driver, Transit, DriverFee, Address, Client, CarType
from money import Money
from repository.address_repository import AddressRepositoryImp
from repository.client_repository import ClientRepositoryImp
from repository.driver_fee_repository import DriverFeeRepositoryImp
from repository.transit_repository import TransitRepositoryImp
from service.car_type_service import CarTypeService
from service.driver_service import DriverService


class DependencyResolver:
    dependency_cache: Dict[str, Any]

    def __init__(self):
        self.dependency_cache = {}

    def resolve_dependency(self, container: Any):
        container_key = str(container)
        if container_key in self.dependency_cache:
            return self.dependency_cache[container_key]
        if isinstance(container, (Depends,)):
            new_container = container.dependency()
            if inspect.isgenerator(new_container):
                new_generator = next(new_container)
                self.dependency_cache[container_key] = new_generator
                return new_generator
            for name, parameter in inspect.signature(new_container.__init__).parameters.items():
                if parameter.default and isinstance(parameter.default, (Depends,)):
                    new_container.__dict__[name] = self.resolve_dependency(parameter.default)
            self.dependency_cache[container_key] = new_container
            return new_container
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

    def __init__(
        self,
        transit_repository: TransitRepositoryImp = Depends(TransitRepositoryImp),
        fee_repository: DriverFeeRepositoryImp = Depends(DriverFeeRepositoryImp),
        driver_service: DriverService = Depends(DriverService),
        client_repository: ClientRepositoryImp = Depends(ClientRepositoryImp),
        address_repository: AddressRepositoryImp = Depends(AddressRepositoryImp),
        car_type_service: CarTypeService = Depends(CarTypeService),
    ):
        self.transit_repository = transit_repository
        self.fee_repository = fee_repository
        self.driver_service = driver_service
        self.client_repository = client_repository
        self.address_repository = address_repository
        self.car_type_service = car_type_service

    def a_client(self) -> Client:
        return self.client_repository.save(Client())

    def a_transit(self, driver: Driver, price: int, when: datetime) -> Transit:
        transit: Transit = Transit(
            address_from=None,
            address_to=None,
            client=None,
            car_class=None,
            date_time=when.astimezone(pytz.UTC),
            distance=Distance.ZERO,
        )
        transit.set_price(Money(price))
        transit.propose_to(driver)
        transit.accept_by(driver, datetime.now())
        return self.transit_repository.save(transit)

    def a_transit_now(self, driver: Driver, price: int) -> Transit:
        return self.a_transit(driver, price, datetime.now())

    def driver_has_min_fee(self, driver: Driver, fee_type: DriverFee.FeeType, amount: int, min: int):
        driver_fee = DriverFee()
        driver_fee.driver = driver
        driver_fee.amount = amount
        driver_fee.fee_type = fee_type
        driver_fee.set_min(Money(min))
        return self.fee_repository.save(driver_fee)

    def driver_has_fee(self, driver: Driver, fee_type: DriverFee.FeeType, amount: int) -> DriverFee:
        return self.driver_has_min_fee(driver, fee_type, amount, 0)

    def a_driver(self) -> Driver:
        return self.driver_service.create_driver(
            "FARME100165AB5EW",
            "Kowalsi",
            "Janusz",
            Driver.Type.REGULAR,
            Driver.Status.ACTIVE,
            "",
        )

    def a_completed_transit_at(self, price: int, when: datetime):
        transit = Transit(
            address_from=Address(country="Polska", city="Warszawa", street="Młynarska", building_number=20),
            address_to=Address(country="Polska", city="Warszawa", street="Zytnia", building_number=20),
            client=self.a_client(),
            car_class=None,
            date_time=datetime.now(),
            distance=Distance.ZERO,
        )
        transit.set_date_time(when)
        transit.client = self.a_client()
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
