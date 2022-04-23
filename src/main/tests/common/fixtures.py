import inspect
from datetime import datetime
from typing import Any, Dict

import pytz
from fastapi.params import Depends

from entity import Driver, Transit, DriverFee
from money import Money
from repository.driver_fee_repository import DriverFeeRepositoryImp
from repository.transit_repository import TransitRepositoryImp
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

    def __init__(
        self,
        transit_repository: TransitRepositoryImp = Depends(TransitRepositoryImp),
        fee_repository: DriverFeeRepositoryImp = Depends(DriverFeeRepositoryImp),
        driver_service: DriverService = Depends(DriverService),
    ):
        self.transit_repository = transit_repository
        self.fee_repository = fee_repository
        self.driver_service = driver_service

    def a_transit(self, driver: Driver, price: int, when: datetime) -> Transit:
        transit: Transit = Transit()
        transit.set_price(Money(price))
        transit.driver = driver
        transit.date_time = when.astimezone(pytz.UTC)
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

