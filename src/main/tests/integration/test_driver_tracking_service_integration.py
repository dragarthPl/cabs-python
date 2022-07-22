from datetime import datetime
from unittest import TestCase

import pytz
from fastapi.params import Depends
from dateutil.relativedelta import relativedelta
from freezegun import freeze_time

from core.database import create_db_and_tables, drop_db_and_tables
from distance.distance import Distance
from entity import Driver
from service.driver_tracking_service import DriverTrackingService
from tests.common.fixtures import DependencyResolver, Fixtures

dependency_resolver = DependencyResolver()


class TestDriverTrackingServiceIntegration(TestCase):
    NOON = datetime(1989, 12, 12, 12, 12).astimezone(pytz.utc)
    NOON_FIVE = NOON + relativedelta(minutes=5)

    driver_tracking_service: DriverTrackingService = dependency_resolver.resolve_dependency(
        Depends(DriverTrackingService)
    )

    fixtures: Fixtures = dependency_resolver.resolve_dependency(Depends(Fixtures))

    def setUp(self):
        create_db_and_tables()

    def test_can_calculate_travelled_distance_from_short_transit(self):
        # given
        driver: Driver = self.fixtures.an_active_regular_driver()
        # and
        with freeze_time(self.NOON):
            # and
            self.driver_tracking_service.register_position(driver.id, 53.32055555555556, -1.7297222222222221, self.NOON)
            self.driver_tracking_service.register_position(driver.id, 53.31861111111111, -1.6997222222222223, self.NOON)
            self.driver_tracking_service.register_position(driver.id, 53.32055555555556, -1.7297222222222221, self.NOON)

            # when
            distance: Distance = self.driver_tracking_service.calculate_travelled_distance(
                driver.id, self.NOON, self.NOON_FIVE)

            # then
            self.assertEqual("4.009km", distance.print_in("km"))

    def tearDown(self) -> None:
        drop_db_and_tables()
