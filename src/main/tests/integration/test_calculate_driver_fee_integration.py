from datetime import datetime
from unittest import TestCase

import pytz
from fastapi.params import Depends
from core.database import create_db_and_tables, drop_db_and_tables
from entity import Driver, Transit, DriverFee
from money import Money

from repository.driver_fee_repository import DriverFeeRepositoryImp
from repository.transit_repository import TransitRepositoryImp
from service.driver_fee_service import DriverFeeService
from service.driver_service import DriverService
from tests.fixtures import DependencyResolver


dependency_resolver = DependencyResolver()


class TestCalculateDriverFeeIntegration(TestCase):
    driver_fee_service: DriverFeeService = dependency_resolver.resolve_dependency(Depends(DriverFeeService))
    fee_repository: DriverFeeRepositoryImp = dependency_resolver.resolve_dependency(Depends(DriverFeeRepositoryImp))
    transit_repository: TransitRepositoryImp = dependency_resolver.resolve_dependency(Depends(TransitRepositoryImp))
    driver_service: DriverService = dependency_resolver.resolve_dependency(Depends(DriverService))

    def setUp(self):
        create_db_and_tables()

    def test_should_calculate_drivers_flat_fee(self):
        # given
        driver = self.a_driver()
        # and
        transit = self.a_transit(driver, 60)
        # and
        self.driver_has_fee(driver, DriverFee.FeeType.FLAT, 10)

        # when
        fee: Money = self.driver_fee_service.calculate_driver_fee(transit.id)

        # then
        self.assertEqual(Money(50), fee)

    def test_should_calculate_drivers_percentage_fee(self):
        # given
        driver = self.a_driver()
        # and
        transit = self.a_transit(driver, 80)
        # and
        self.driver_has_fee(driver, DriverFee.FeeType.PERCENTAGE, 50)

        # when
        fee: Money = self.driver_fee_service.calculate_driver_fee(transit.id)

        # then
        self.assertEqual(Money(40), fee)

    def test_should_use_minimum_fee(self):
        # given
        driver = self.a_driver()
        # and
        transit = self.a_transit(driver, 10)
        # and
        self._driver_has_fee(driver, DriverFee.FeeType.PERCENTAGE, 7, 5)

        # when
        fee: Money = self.driver_fee_service.calculate_driver_fee(transit.id)

        # then
        self.assertEqual(Money(5), fee)

    def a_driver(self) -> Driver:
        return self.driver_service.create_driver(
            "FARME100165AB5EW",
            "Kowalsi",
            "Janusz",
            Driver.Type.REGULAR,
            Driver.Status.ACTIVE,
            "",
        )

    def _driver_has_fee(self, driver: Driver, fee_type: DriverFee.FeeType, amount: int, min: int):
        driver_fee = DriverFee()
        driver_fee.driver = driver
        driver_fee.amount = amount
        driver_fee.fee_type = fee_type
        driver_fee.min = min
        return self.fee_repository.save(driver_fee)

    def driver_has_fee(self, driver: Driver, fee_type: DriverFee.FeeType, amount: int) -> DriverFee:
        return self._driver_has_fee(driver, fee_type, amount, 0)

    def a_transit(self, driver: Driver, price: int) -> Transit:
        transit: Transit = Transit()
        transit.price = price
        transit.driver = driver
        transit.date_time = datetime(2020, 10, 20, 0, 0, 0).astimezone(pytz.UTC)
        return self.transit_repository.save(transit)

    def tearDown(self) -> None:
        drop_db_and_tables()
