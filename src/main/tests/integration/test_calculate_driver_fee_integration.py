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
from tests.common.fixtures import DependencyResolver, Fixtures

dependency_resolver = DependencyResolver()


class TestCalculateDriverFeeIntegration(TestCase):
    fixtures: Fixtures = dependency_resolver.resolve_dependency(Depends(Fixtures))
    driver_fee_service: DriverFeeService = dependency_resolver.resolve_dependency(Depends(DriverFeeService))

    def setUp(self):
        create_db_and_tables()

    def test_should_calculate_drivers_flat_fee(self):
        # given
        driver = self.fixtures.a_driver()
        # and
        transit = self.fixtures.a_transit_now(driver, 60)
        # and
        self.fixtures.driver_has_fee(driver, DriverFee.FeeType.FLAT, 10)

        # when
        fee: Money = self.driver_fee_service.calculate_driver_fee(transit.id)

        # then
        self.assertEqual(Money(50), fee)

    def test_should_calculate_drivers_percentage_fee(self):
        # given
        driver = self.fixtures.a_driver()
        # and
        transit = self.fixtures.a_transit_now(driver, 80)
        # and
        self.fixtures.driver_has_fee(driver, DriverFee.FeeType.PERCENTAGE, 50)

        # when
        fee: Money = self.driver_fee_service.calculate_driver_fee(transit.id)

        # then
        self.assertEqual(Money(40), fee)

    def test_should_use_minimum_fee(self):
        # given
        driver = self.fixtures.a_driver()
        # and
        transit = self.fixtures.a_transit_now(driver, 10)
        # and
        self.fixtures.driver_has_min_fee(driver, DriverFee.FeeType.PERCENTAGE, 7, 5)

        # when
        fee: Money = self.driver_fee_service.calculate_driver_fee(transit.id)

        # then
        self.assertEqual(Money(5), fee)

    def tearDown(self) -> None:
        drop_db_and_tables()
