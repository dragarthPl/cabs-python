from datetime import datetime
from typing import Dict
from unittest import TestCase

import pytz
from fastapi.params import Depends

from core.const import Month
from core.database import create_db_and_tables, drop_db_and_tables
from entity import Driver, Transit, DriverFee
from money import Money
from repository.address_repository import AddressRepositoryImp
from repository.client_repository import ClientRepositoryImp
from repository.driver_fee_repository import DriverFeeRepositoryImp
from repository.transit_repository import TransitRepositoryImp
from service.driver_service import DriverService
from tests.fixtures import DependencyResolver

dependency_resolver = DependencyResolver()


class TestCalculateDriverPeriodicPaymentsIntegration(TestCase):
    driver_service: DriverService = dependency_resolver.resolve_dependency(Depends(DriverService))
    transit_repository: TransitRepositoryImp = dependency_resolver.resolve_dependency(Depends(TransitRepositoryImp))
    fee_repository: DriverFeeRepositoryImp = dependency_resolver.resolve_dependency(Depends(DriverFeeRepositoryImp))
    address_repository: AddressRepositoryImp = dependency_resolver.resolve_dependency(Depends(AddressRepositoryImp))
    client_repository: ClientRepositoryImp = dependency_resolver.resolve_dependency(Depends(ClientRepositoryImp))

    def setUp(self):
        create_db_and_tables()

    def test_calculate_monthly_payment(self):
        # Given
        driver: Driver = self.a_driver()
        # and
        self.a_transit(driver, 60, datetime(2000, 10, 1, 6, 30))
        self.a_transit(driver, 70, datetime(2000, 10, 1, 2, 30))
        self.a_transit(driver, 80, datetime(2000, 10, 1, 6, 30))
        self.a_transit(driver, 60, datetime(2000, 11, 1, 1, 30))
        self.a_transit(driver, 30, datetime(2000, 11, 1, 1, 30))
        self.a_transit(driver, 15, datetime(2000, 12, 1, 2, 30))
        # and
        self.driver_has_fee(driver, DriverFee.FeeType.FLAT, 10)

        # When
        fee_october = self.driver_service.calculate_driver_monthly_payment(driver.id, 2000, 10)
        # Then
        self.assertEqual(Money(180), fee_october)

        # when
        fee_october = self.driver_service.calculate_driver_monthly_payment(driver.id, 2000, 11)
        # then
        self.assertEqual(Money(70), fee_october)

        # when
        fee_october = self.driver_service.calculate_driver_monthly_payment(driver.id, 2000, 12)
        # then
        self.assertEqual(Money(5), fee_october)

    def test_calculate_yearly_payment(self):
        # Given
        driver: Driver = self.a_driver()
        # and
        self.a_transit(driver, 60, datetime(2000, 10, 1, 6, 30))
        self.a_transit(driver, 70, datetime(2000, 10, 10, 2, 30))
        self.a_transit(driver, 80, datetime(2000, 10, 30, 6, 30))
        self.a_transit(driver, 60, datetime(2000, 11, 10, 1, 30))
        self.a_transit(driver, 30, datetime(2000, 11, 10, 1, 30))
        self.a_transit(driver, 15, datetime(2000, 12, 10, 2, 30))

        # and
        self.driver_has_fee(driver, DriverFee.FeeType.FLAT, 10)

        # when
        payments: Dict[int, Money] = self.driver_service.calculate_driver_yearly_payment(driver.id, 2000)

        # then
        self.assertEqual(Money.ZERO, payments.get(Month.JANUARY))
        self.assertEqual(Money.ZERO, payments.get(Month.FEBRUARY))
        self.assertEqual(Money.ZERO, payments.get(Month.MARCH))
        self.assertEqual(Money.ZERO, payments.get(Month.APRIL))
        self.assertEqual(Money.ZERO, payments.get(Month.MAY))
        self.assertEqual(Money.ZERO, payments.get(Month.JUNE))
        self.assertEqual(Money.ZERO, payments.get(Month.JULY))
        self.assertEqual(Money.ZERO, payments.get(Month.AUGUST))
        self.assertEqual(Money.ZERO, payments.get(Month.SEPTEMBER))
        self.assertEqual(Money(180), payments.get(Month.OCTOBER))
        self.assertEqual(Money(70), payments.get(Month.NOVEMBER))
        self.assertEqual(Money(5), payments.get(Month.DECEMBER))

    def a_transit(self, driver: Driver, price: int, when: datetime) -> Transit:
        transit: Transit = Transit()
        transit.price = price
        transit.driver = driver
        transit.date_time = when.astimezone(pytz.UTC)
        return self.transit_repository.save(transit)

    def _driver_has_fee(self, driver: Driver, fee_type: DriverFee.FeeType, amount: int, min: int):
        driver_fee = DriverFee()
        driver_fee.driver = driver
        driver_fee.amount = amount
        driver_fee.fee_type = fee_type
        driver_fee.min = min
        return self.fee_repository.save(driver_fee)

    def driver_has_fee(self, driver: Driver, fee_type: DriverFee.FeeType, amount: int) -> DriverFee:
        return self._driver_has_fee(driver, fee_type, amount, 0)

    def a_driver(self) -> Driver:
        return self.driver_service.create_driver(
            "FARME100165AB5EW",
            "Kowalsi",
            "Janusz",
            Driver.Type.REGULAR,
            Driver.Status.ACTIVE,
            "",
        )

    def tearDown(self) -> None:
        drop_db_and_tables()
