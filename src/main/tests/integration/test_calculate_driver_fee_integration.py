from unittest import TestCase

from core.database import create_db_and_tables, drop_db_and_tables
from driverfleet.driver_fee import DriverFee
from money import Money

from driverfleet.driver_fee_service import DriverFeeService
from tests.common.fixtures import DependencyResolver, Fixtures

dependency_resolver = DependencyResolver()


class TestCalculateDriverFeeIntegration(TestCase):
    fixtures: Fixtures = dependency_resolver.resolve_dependency(Fixtures)
    driver_fee_service: DriverFeeService = dependency_resolver.resolve_dependency(DriverFeeService)

    def setUp(self):
        create_db_and_tables()

    def test_should_calculate_drivers_flat_fee(self):
        # given
        driver = self.fixtures.an_active_regular_driver()
        # and
        self.fixtures.driver_has_fee(driver, DriverFee.FeeType.FLAT, 10)

        # when
        fee: Money = self.driver_fee_service.calculate_driver_fee(Money(60), driver.id)

        # then
        self.assertEqual(Money(50), fee)

    def test_should_calculate_drivers_percentage_fee(self):
        # given
        driver = self.fixtures.an_active_regular_driver()
        # and
        self.fixtures.driver_has_fee(driver, DriverFee.FeeType.PERCENTAGE, 50)

        # when
        fee: Money = self.driver_fee_service.calculate_driver_fee(Money(80), driver.id)

        # then
        self.assertEqual(Money(40), fee)

    def test_should_use_minimum_fee(self):
        # given
        driver = self.fixtures.an_active_regular_driver()
        # and
        self.fixtures.driver_has_min_fee(driver, DriverFee.FeeType.PERCENTAGE, 7, 5)

        # when
        fee: Money = self.driver_fee_service.calculate_driver_fee(Money(10), driver.id)

        # then
        self.assertEqual(Money(5), fee)

    def tearDown(self) -> None:
        drop_db_and_tables()
