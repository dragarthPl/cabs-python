from datetime import datetime
from unittest import TestCase

import pytz
from fastapi.params import Depends
from freezegun import freeze_time

from core.database import create_db_and_tables, drop_db_and_tables
from dto.address_dto import AddressDTO
from dto.client_dto import ClientDTO
from dto.transit_dto import TransitDTO
from entity import Client
from service.transit_service import TransitService
from tests.common.fixtures import Fixtures, DependencyResolver
from ui.transit_controller import TransitController

dependency_resolver = DependencyResolver()

class TestTariffRecognizingIntegration(TestCase):
    fixtures: Fixtures = dependency_resolver.resolve_dependency(Fixtures)
    transit_controller: TransitController = TransitController(
        transit_service=dependency_resolver.resolve_dependency(TransitService)
    )

    def setUp(self):
        create_db_and_tables()

    def test_new_years_eve_tariff_should_be_displayed(self):
        # given
        transit_dto: TransitDTO = self.create_transit(datetime(2021, 12, 31, 8, 30).astimezone(pytz.utc))

        # when
        transit_dto = self.transit_controller.get_transit(transit_dto.id)

        # then
        self.assertEqual("Sylwester", transit_dto.tariff)
        self.assertEqual(3.5, transit_dto.km_rate)

    def test_weekend_tariff_should_be_displayed(self):
        # given
        transit_dto: TransitDTO = self.create_transit(datetime(2021, 4, 17, 8, 30).astimezone(pytz.utc))

        # when
        transit_dto = self.transit_controller.get_transit(transit_dto.id)

        # then
        self.assertEqual("Weekend", transit_dto.tariff)
        self.assertEqual(1.5, transit_dto.km_rate)

    def test_weekend_plus_tariff_should_be_displayed(self):
        # given
        transit_dto: TransitDTO = self.create_transit(datetime(2021, 4, 17, 22, 30).astimezone(pytz.utc))

        # when
        transit_dto = self.transit_controller.get_transit(transit_dto.id)

        # then
        self.assertEqual("Weekend+", transit_dto.tariff)
        self.assertEqual(2.5, transit_dto.km_rate)

    def test_standard_tariff_should_be_displayed(self):
        # given
        transit_dto: TransitDTO = self.create_transit(datetime(2021, 4, 13, 22, 30).astimezone(pytz.utc))

        # when
        transit_dto = self.transit_controller.get_transit(transit_dto.id)

        # then
        self.assertEqual("Standard", transit_dto.tariff)
        self.assertEqual(1.0, transit_dto.km_rate)

    def create_transit(self, when: datetime) -> TransitDTO:
        client: Client = self.fixtures.a_client()
        with freeze_time(when, tz_offset=2):
            transit_dto: TransitDTO = TransitDTO()
            destination: AddressDTO = AddressDTO(
                country="Polska", city="Warszawa", street="Zytnia", building_number=20)
            address_from: AddressDTO = AddressDTO(
                country="Polska", city="Warszawa", street="Młynarska", building_number=20)
            transit_dto.address_from = address_from
            transit_dto.address_to = destination
            client_dto: ClientDTO = ClientDTO()
            client_dto.id = client.id
            transit_dto.client_dto = client_dto
            return self.transit_controller.create_transit(transit_dto)

    def tearDown(self) -> None:
        drop_db_and_tables()
