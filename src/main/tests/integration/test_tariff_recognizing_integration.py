from datetime import datetime
from unittest import TestCase

import pytz
from fastapi.params import Depends

from core.database import create_db_and_tables, drop_db_and_tables
from dto.transit_dto import TransitDTO
from service.transit_service import TransitService
from tests.common.fixtures import Fixtures, DependencyResolver
from ui.transit_controller import TransitController

dependency_resolver = DependencyResolver()

class TestTariffRecognizingIntegration(TestCase):
    fixtures: Fixtures = dependency_resolver.resolve_dependency(Depends(Fixtures))
    transit_controller: TransitController = TransitController(
        transit_service=dependency_resolver.resolve_dependency(Depends(TransitService))
    )

    def setUp(self):
        create_db_and_tables()

    def test_new_years_eve_tariff_should_be_displayed(self):
        # given
        transit = self.fixtures.a_completed_transit_at(60, datetime(2021, 12, 31, 8, 30).astimezone(pytz.utc))

        # when
        transit_dto: TransitDTO = self.transit_controller.get_transit(transit.id)

        # then
        self.assertEqual("Sylwester", transit_dto.tariff)
        self.assertEqual(3.5, transit_dto.km_rate)

    def test_weekend_tariff_should_be_displayed(self):
        # given
        transit = self.fixtures.a_completed_transit_at(60, datetime(2021, 4, 17, 8, 30).astimezone(pytz.utc))

        # when
        transit_dto: TransitDTO = self.transit_controller.get_transit(transit.id)

        # then
        self.assertEqual("Weekend", transit_dto.tariff)
        self.assertEqual(1.5, transit_dto.km_rate)

    def test_weekend_plus_tariff_should_be_displayed(self):
        # given
        transit = self.fixtures.a_completed_transit_at(60, datetime(2021, 4, 17, 22, 30).astimezone(pytz.utc))

        # when
        transit_dto: TransitDTO = self.transit_controller.get_transit(transit.id)

        # then
        self.assertEqual("Weekend+", transit_dto.tariff)
        self.assertEqual(2.5, transit_dto.km_rate)

    def test_standard_tariff_should_be_displayed(self):
        # given
        transit = self.fixtures.a_completed_transit_at(60, datetime(2021, 4, 13, 22, 30).astimezone(pytz.utc))

        # when
        transit_dto: TransitDTO = self.transit_controller.get_transit(transit.id)

        # then
        self.assertEqual("Standard", transit_dto.tariff)
        self.assertEqual(1.0, transit_dto.km_rate)

    def test_standard_tariff_should_be_displayed_before_2019(self):
        # given
        transit = self.fixtures.a_completed_transit_at(60, datetime(2018, 12, 31, 8, 30).astimezone(pytz.utc))

        # when
        transit_dto: TransitDTO = self.transit_controller.get_transit(transit.id)

        # then
        self.assertEqual("Standard", transit_dto.tariff)
        self.assertEqual(1.0, transit_dto.km_rate)

    def tearDown(self) -> None:
        drop_db_and_tables()
