from datetime import datetime
from unittest import TestCase

import pytz
from dateutil.relativedelta import relativedelta

from freezegun import freeze_time

from core.database import create_db_and_tables, drop_db_and_tables
from driverfleet.driver import Driver
from driverfleet.driverreport.travelleddistance.travelled_distance_service import TravelledDistanceService
from tracking.driver_position import DriverPosition

from tests.common.fixtures import DependencyResolver, Fixtures

dependency_resolver = DependencyResolver()


class TestCalculateDriverTravelledDistanceIntegration(TestCase):
    NOON = datetime(1989, 12, 12, 12, 12).astimezone(pytz.utc)
    NOON_FIVE = NOON + relativedelta(minutes=5)
    NOON_TEN = NOON_FIVE + relativedelta(minutes=5)

    travelled_distance_service: TravelledDistanceService = dependency_resolver.resolve_dependency(
        TravelledDistanceService
    )

    fixtures: Fixtures = dependency_resolver.resolve_dependency(Fixtures)

    def setUp(self):
        create_db_and_tables()

    def test_distance_is_zero_when_zero_positions(self):
        # given
        driver = self.fixtures.an_active_regular_driver()

        # when
        distance = self.travelled_distance_service.calculate_distance(driver.id, self.NOON, self.NOON_FIVE)

        # then
        self.assertEqual("0km", distance.print_in("km"))

    def test_travelled_distance_without_multiple_positions_iz_zero(self):
        # given
        driver = self.fixtures.an_active_regular_driver()
        # and
        with freeze_time(self.NOON):
            self.travelled_distance_service.add_position(driver.id, 53.32055555555556, -1.7297222222222221, self.NOON)

        # when
        distance = self.travelled_distance_service.calculate_distance(driver.id, self.NOON, self.NOON_FIVE)

        # then
        self.assertEqual("0km", distance.print_in("km"))

    def test_can_calculate_travelled_distance_from_short_transit(self):
        # given
        driver = self.fixtures.an_active_regular_driver()
        # and
        with freeze_time(self.NOON):
            self.travelled_distance_service.add_position(driver.id, 53.32055555555556, -1.7297222222222221, self.NOON)
            self.travelled_distance_service.add_position(driver.id, 53.31861111111111, -1.6997222222222223, self.NOON)
            self.travelled_distance_service.add_position(driver.id, 53.32055555555556, -1.7297222222222221, self.NOON)

            # when
            distance = self.travelled_distance_service.calculate_distance(driver.id, self.NOON, self.NOON_FIVE)

            # then
            self.assertEqual("4.009km", distance.print_in("km"))

    def test_can_calculate_travelled_distance_from_long_transit(self):
        # given
        driver = self.fixtures.an_active_regular_driver()
        with freeze_time(self.NOON):
            # and
            self.travelled_distance_service.add_position(driver.id, 53.32055555555556, -1.7297222222222221, self.NOON)
            self.travelled_distance_service.add_position(driver.id, 53.31861111111111, -1.6997222222222223, self.NOON)
            self.travelled_distance_service.add_position(driver.id, 53.32055555555556, -1.7297222222222221, self.NOON)
        with freeze_time(self.NOON_FIVE):
            # and
            self.travelled_distance_service.add_position(
                driver.id, 53.32055555555556, -1.7297222222222221, self.NOON_FIVE)
            self.travelled_distance_service.add_position(
                driver.id, 53.31861111111111, -1.6997222222222223, self.NOON_FIVE)
            self.travelled_distance_service.add_position(
                driver.id, 53.32055555555556, -1.7297222222222221, self.NOON_FIVE)

        # when
        distance = self.travelled_distance_service.calculate_distance(driver.id, self.NOON, self.NOON_FIVE)

        # then
        self.assertEqual("8.017km", distance.print_in("km"))

    def test_can_calculate_travelled_distance_with_multiple_breaks(self):
        # given
        driver = self.fixtures.an_active_regular_driver()
        with freeze_time(self.NOON):
            # and
            self.travelled_distance_service.add_position(driver.id, 53.32055555555556, -1.7297222222222221, self.NOON)
            self.travelled_distance_service.add_position(driver.id, 53.31861111111111, -1.6997222222222223, self.NOON)
            self.travelled_distance_service.add_position(driver.id, 53.32055555555556, -1.7297222222222221, self.NOON)
        with freeze_time(self.NOON_FIVE):
            # and
            self.travelled_distance_service.add_position(
               driver.id, 53.32055555555556, -1.7297222222222221, self.NOON_FIVE)
            self.travelled_distance_service.add_position(
               driver.id, 53.31861111111111, -1.6997222222222223, self.NOON_FIVE)
            self.travelled_distance_service.add_position(
               driver.id, 53.32055555555556, -1.7297222222222221, self.NOON_FIVE)
        with freeze_time(self.NOON_TEN):
            # and
            self.travelled_distance_service.add_position(
                driver.id, 53.32055555555556, -1.7297222222222221, self.NOON_TEN)
            self.travelled_distance_service.add_position(
                driver.id, 53.31861111111111, -1.6997222222222223, self.NOON_TEN)
            self.travelled_distance_service.add_position(
                driver.id, 53.32055555555556, -1.7297222222222221, self.NOON_TEN)

        # when
        distance = self.travelled_distance_service.calculate_distance(driver.id, self.NOON, self.NOON_TEN)

        # then
        self.assertEqual("12.026km", distance.print_in("km"))

    def tearDown(self) -> None:
        drop_db_and_tables()

