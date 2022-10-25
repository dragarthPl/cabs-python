from datetime import datetime
from typing import Dict
from unittest import TestCase

from core.const import Month
from core.database import create_db_and_tables, drop_db_and_tables
from driverfleet.driver import Driver
from driverfleet.driver_fee import DriverFee
from money import Money
from driverfleet.driver_service import DriverService
from tests.common.fixtures import DependencyResolver, Fixtures

dependency_resolver = DependencyResolver()


class TestCalculateDriverPeriodicPaymentsIntegration(TestCase):
    fixtures: Fixtures = dependency_resolver.resolve_dependency(Fixtures)
    driver_service: DriverService = dependency_resolver.resolve_dependency(DriverService)

    def setUp(self):
        create_db_and_tables()

    def test_calculate_monthly_payment(self):
        # Given
        driver: Driver = self.fixtures.an_active_regular_driver()
        # and
        self.fixtures.transit_details(driver, 60, datetime(2000, 10, 1, 6, 30))
        self.fixtures.transit_details(driver, 70, datetime(2000, 10, 1, 2, 30))
        self.fixtures.transit_details(driver, 80, datetime(2000, 10, 1, 6, 30))
        self.fixtures.transit_details(driver, 60, datetime(2000, 11, 1, 1, 30))
        self.fixtures.transit_details(driver, 30, datetime(2000, 11, 1, 1, 30))
        self.fixtures.transit_details(driver, 15, datetime(2000, 12, 1, 2, 30))
        # and
        self.fixtures.driver_has_fee(driver, DriverFee.FeeType.FLAT, 10)

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
        driver: Driver = self.fixtures.an_active_regular_driver()
        # and
        self.fixtures.transit_details(driver, 60, datetime(2000, 10, 1, 6, 30))
        self.fixtures.transit_details(driver, 70, datetime(2000, 10, 10, 2, 30))
        self.fixtures.transit_details(driver, 80, datetime(2000, 10, 30, 6, 30))
        self.fixtures.transit_details(driver, 60, datetime(2000, 11, 10, 1, 30))
        self.fixtures.transit_details(driver, 30, datetime(2000, 11, 10, 1, 30))
        self.fixtures.transit_details(driver, 15, datetime(2000, 12, 10, 2, 30))

        # and
        self.fixtures.driver_has_fee(driver, DriverFee.FeeType.FLAT, 10)

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

    def tearDown(self) -> None:
        drop_db_and_tables()
