from datetime import datetime
from typing import List, Tuple, Iterable, Any
from unittest import IsolatedAsyncioTestCase

import fastapi
import pytest
import pytz
import time
from fastapi.params import Depends
from fastapi_events import middleware_identifier
from freezegun import freeze_time
from mockito import when, ANY
from httpx import AsyncClient

from core.database import create_db_and_tables, drop_db_and_tables
from dto.analyzed_addresses_dto import AnalyzedAddressesDTO
from entity import CarType, Client, Driver, Address
from repository.address_repository import AddressRepositoryImp
from service.geocoding_service import GeocodingService
from transitanalyzer.graph_transit_analyzer import GraphTransitAnalyzer
from ui.transit_analyzer_controller import TransitAnalyzerController

from tests.common.fixtures import DependencyResolver, Fixtures

from cabs_application import CabsApplication

dependency_resolver = DependencyResolver()


class TestAnalyzeNearbyTransitsIntegration(IsolatedAsyncioTestCase):
    fixtures: Fixtures = dependency_resolver.resolve_dependency(Fixtures)

    transit_analyzer_controller: TransitAnalyzerController = TransitAnalyzerController(
        graph_transit_analyzer=dependency_resolver.resolve_dependency(GraphTransitAnalyzer),
        address_repository=dependency_resolver.resolve_dependency(AddressRepositoryImp)
    )

    geocoding_service: GeocodingService = dependency_resolver.resolve_dependency(GeocodingService)

    async def asyncSetUp(self):
        create_db_and_tables()
        app = CabsApplication().create_app()
        middleware_identifier.set(app.middleware_stack.app._id)

        self.client = AsyncClient(app=app)
        self.fixtures.an_active_car_category(CarType.CarClass.VAN)
        when(self.geocoding_service).geocode_address(ANY).thenReturn([1.0, 1.0])

    @pytest.mark.skip(reason="disabled")
    async def test_can_find_longest_travel(self):
        # given
        client: Client = self.fixtures.a_client()
        # and
        driver: Driver = self.fixtures.a_nearby_driver_default("WA001", 1, 1, CarType.CarClass.VAN, datetime.now())
        with freeze_time(datetime(2021, 1, 1, 0, 0).astimezone(pytz.utc)):
            address1: Address = Address(country="1_1", district="1", city="1", street="1", building_number=1)
            address2: Address = Address(country="1_2", district="2", city="2", street="2", building_number=2)
            address3: Address = Address(country="1_3", district="3", city="3", street="3", building_number=3)
            address4: Address = Address(country="1_4", district="4", city="4", street="4", building_number=3)
            address5: Address = Address(country="1_5", district="5", city="5", street="5", building_number=3)
            # and
            # 1-2-3-4
            self.a_transit_from_to(
                50,
                datetime(2021, 1, 1, 0, 00).astimezone(pytz.utc),
                datetime(2021, 1, 1, 0, 5).astimezone(pytz.utc),
                client,
                driver,
                address1,
                address2,
            )
            self.a_transit_from_to(
                50,
                datetime(2021, 1, 1, 0, 6).astimezone(pytz.utc),
                datetime(2021, 1, 1, 0, 10).astimezone(pytz.utc),
                client,
                driver,
                address2,
                address3,
            )
            self.a_transit_from_to(
                50,
                datetime(2021, 1, 1, 0, 15).astimezone(pytz.utc),
                datetime(2021, 1, 1, 0, 20).astimezone(pytz.utc),
                client,
                driver,
                address3,
                address4,
            )
            # 1-2-3
            self.a_transit_from_to(
                50,
                datetime(2021, 1, 2, 0, 00).astimezone(pytz.utc),
                datetime(2021, 1, 2, 0, 10).astimezone(pytz.utc),
                client,
                driver,
                address1,
                address2,
            )
            self.a_transit_from_to(
                50,
                datetime(2021, 1, 2, 0, 15).astimezone(pytz.utc),
                datetime(2021, 1, 2, 0, 20).astimezone(pytz.utc),
                client,
                driver,
                address2,
                address3,
            )
            # 1-3
            self.a_transit_from_to(
                50,
                datetime(2021, 1, 3, 0, 00).astimezone(pytz.utc),
                datetime(2021, 1, 3, 0, 10).astimezone(pytz.utc),
                client,
                driver,
                address1,
                address3,
            )
            # 3-1-2-5-4-5
            self.a_transit_from_to(
                50,
                datetime(2021, 2, 1, 0, 00).astimezone(pytz.utc),
                datetime(2021, 2, 1, 0, 10).astimezone(pytz.utc),
                client,
                driver,
                address3,
                address1,
            )
            self.a_transit_from_to(
                50,
                datetime(2021, 2, 1, 0, 20).astimezone(pytz.utc),
                datetime(2021, 2, 1, 0, 25).astimezone(pytz.utc),
                client,
                driver,
                address1,
                address2,
            )
            self.a_transit_from_to(
                50,
                datetime(2021, 2, 1, 0, 30).astimezone(pytz.utc),
                datetime(2021, 2, 1, 0, 35).astimezone(pytz.utc),
                client,
                driver,
                address2,
                address5,
            )
            self.a_transit_from_to(
                50,
                datetime(2021, 2, 1, 0, 40).astimezone(pytz.utc),
                datetime(2021, 2, 1, 0, 45).astimezone(pytz.utc),
                client,
                driver,
                address5,
                address4,
            )
            self.a_transit_from_to(
                50,
                datetime(2021, 2, 1, 0, 50).astimezone(pytz.utc),
                datetime(2021, 2, 1, 0, 55).astimezone(pytz.utc),
                client,
                driver,
                address4,
                address5,
            )
            # when
            analyzed_addresses_dto: AnalyzedAddressesDTO = self.transit_analyzer_controller.analyze(
                client.id,
                address1.id
            )
            # then
            # 1-2-5-4-5
            self.addresses_contain_exactly(analyzed_addresses_dto, (address1, address2, address5, address4, address5))

    @pytest.mark.skip(reason="disabled")
    async def test_can_find_longest_travel_from_multiple_clients(self):
        # given
        client1: Client = self.fixtures.a_client()
        client2: Client = self.fixtures.a_client()
        client3: Client = self.fixtures.a_client()
        client4: Client = self.fixtures.a_client()
        # and
        driver: Driver = self.fixtures.a_nearby_driver_default("WA001", 1, 1, CarType.CarClass.VAN, datetime.now())
        # and
        with freeze_time(datetime(2021, 1, 1, 0, 0).astimezone(pytz.utc)):
            address1: Address = Address(country="2_1", district="1", city="1", street="1", building_number=1)
            address2: Address = Address(country="2_2", district="2", city="2", street="2", building_number=2)
            address3: Address = Address(country="2_3", district="3", city="3", street="3", building_number=3)
            address4: Address = Address(country="2_4", district="4", city="4", street="4", building_number=3)
            address5: Address = Address(country="2_5", district="5", city="5", street="5", building_number=3)
            # and
            # 1-2-3-4
            self.a_transit_from_to(
                50,
                datetime(2021, 1, 1, 0, 00).astimezone(pytz.utc),
                datetime(2021, 1, 1, 0, 10).astimezone(pytz.utc),
                client1,
                driver,
                address1,
                address2,
            )
            self.a_transit_from_to(
                50,
                datetime(2021, 1, 1, 0, 15).astimezone(pytz.utc),
                datetime(2021, 1, 1, 0, 20).astimezone(pytz.utc),
                client1,
                driver,
                address2,
                address3,
            )
            self.a_transit_from_to(
                50,
                datetime(2021, 1, 1, 0, 25).astimezone(pytz.utc),
                datetime(2021, 1, 1, 0, 30).astimezone(pytz.utc),
                client1,
                driver,
                address3,
                address4,
            )
            # 1-2-3
            self.a_transit_from_to(
                50,
                datetime(2021, 1, 2, 0, 00).astimezone(pytz.utc),
                datetime(2021, 1, 2, 0, 10).astimezone(pytz.utc),
                client2,
                driver,
                address1,
                address2,
            )
            self.a_transit_from_to(
                50,
                datetime(2021, 1, 2, 0, 15).astimezone(pytz.utc),
                datetime(2021, 1, 2, 0, 20).astimezone(pytz.utc),
                client2,
                driver,
                address2,
                address3,
            )
            # 1-3
            self.a_transit_from_to(
                50,
                datetime(2021, 1, 3, 0, 00).astimezone(pytz.utc),
                datetime(2021, 1, 3, 0, 10).astimezone(pytz.utc),
                client3,
                driver,
                address1,
                address3,
            )
            # 3-1-2-5-4-5
            self.a_transit_from_to(
                50,
                datetime(2021, 2, 1, 0, 00).astimezone(pytz.utc),
                datetime(2021, 2, 1, 0, 10).astimezone(pytz.utc),
                client4,
                driver,
                address3,
                address1,
            )
            self.a_transit_from_to(
                50,
                datetime(2021, 2, 1, 0, 20).astimezone(pytz.utc),
                datetime(2021, 2, 1, 0, 25).astimezone(pytz.utc),
                client4,
                driver,
                address1,
                address2,
            )
            self.a_transit_from_to(
                50,
                datetime(2021, 2, 1, 0, 30).astimezone(pytz.utc),
                datetime(2021, 2, 1, 0, 35).astimezone(pytz.utc),
                client4,
                driver,
                address2,
                address5,
            )
            self.a_transit_from_to(
                50,
                datetime(2021, 2, 1, 0, 40).astimezone(pytz.utc),
                datetime(2021, 2, 1, 0, 45).astimezone(pytz.utc),
                client4,
                driver,
                address5,
                address4,
            )
            self.a_transit_from_to(
                50,
                datetime(2021, 2, 1, 0, 50).astimezone(pytz.utc),
                datetime(2021, 2, 1, 0, 55).astimezone(pytz.utc),
                client4,
                driver,
                address4,
                address5,
            )

            # when
            analyzed_addresses_dto: AnalyzedAddressesDTO = self.transit_analyzer_controller.analyze(
                client1.id,
                address1.id
            )

            # then
            # 1-2-3-4
            self.addresses_contain_exactly(analyzed_addresses_dto, (address1, address2, address3, address4))

    @pytest.mark.skip(reason="disabled")
    @freeze_time(datetime(2021, 1, 1, 0, 0).astimezone(pytz.utc))
    async def test_can_find_longest_travel_with_long_stops(self):
        # given
        client: Client = self.fixtures.a_client()
        # and
        driver: Driver = self.fixtures.a_nearby_driver_default("WA001", 1, 1, CarType.CarClass.VAN, datetime.now())
        # and
        with freeze_time(datetime(2021, 1, 1, 0, 0).astimezone(pytz.utc)):
            address1: Address = Address(country="3_1", district="1", city="1", street="1", building_number=1)
            address2: Address = Address(country="3_2", district="2", city="2", street="2", building_number=2)
            address3: Address = Address(country="3_3", district="3", city="3", street="3", building_number=3)
            address4: Address = Address(country="3_4", district="4", city="4", street="4", building_number=3)
            address5: Address = Address(country="3_5", district="5", city="5", street="5", building_number=3)
            # and
            # 1-2-3-4-(stop)-5-1
            self.a_transit_from_to(
                50,
                datetime(2021, 2, 1, 0, 0).astimezone(pytz.utc),
                datetime(2021, 2, 1, 0, 5).astimezone(pytz.utc),
                client,
                driver,
                address1,
                address2,
            )
            self.a_transit_from_to(
                50,
                datetime(2021, 2, 1, 0, 10).astimezone(pytz.utc),
                datetime(2021, 2, 1, 0, 15).astimezone(pytz.utc),
                client,
                driver,
                address2,
                address3,
            )
            self.a_transit_from_to(
                50,
                datetime(2021, 2, 1, 0, 20).astimezone(pytz.utc),
                datetime(2021, 2, 1, 0, 25).astimezone(pytz.utc),
                client,
                driver,
                address3,
                address4,
            )
            self.a_transit_from_to(
                50,
                datetime(2021, 2, 1, 1, 0).astimezone(pytz.utc),
                datetime(2021, 2, 1, 1, 10).astimezone(pytz.utc),
                client,
                driver,
                address4,
                address5,
            )
            self.a_transit_from_to(
                50,
                datetime(2021, 2, 1, 1, 10).astimezone(pytz.utc),
                datetime(2021, 2, 1, 1, 15).astimezone(pytz.utc),
                client,
                driver,
                address5,
                address1,
            )

            # when
            analyzed_addresses_dto: AnalyzedAddressesDTO = self.transit_analyzer_controller.analyze(
                client.id,
                address1.id
            )

            # then
            # 1-2-3-4
            self.addresses_contain_exactly(analyzed_addresses_dto, (address1, address2, address3, address4))

    @pytest.mark.skip(reason="disabled")
    @freeze_time(datetime(2021, 1, 1, 0, 0).astimezone(pytz.utc))
    async def test_can_find_longest_travel_with_loops(self):
        # given
        client: Client = self.fixtures.a_client()
        # and
        driver: Driver = self.fixtures.a_nearby_driver_default("WA001", 1, 1, CarType.CarClass.VAN, datetime.now())
        # and
        with freeze_time(datetime(2021, 1, 1, 0, 0).astimezone(pytz.utc)):
            address1: Address = Address(country="4_1", district="1", city="1", street="1", building_number=1)
            address2: Address = Address(country="4_2", district="2", city="2", street="2", building_number=2)
            address3: Address = Address(country="4_3", district="3", city="3", street="3", building_number=3)
            address4: Address = Address(country="4_4", district="4", city="4", street="4", building_number=3)
            address5: Address = Address(country="4_5", district="5", city="5", street="5", building_number=3)
            # and
            # 5-1-2-3
            self.a_transit_from_to(
                50,
                datetime(2021, 1, 1, 0, 00).astimezone(pytz.utc),
                datetime(2021, 1, 1, 0, 5).astimezone(pytz.utc),
                client,
                driver,
                address5,
                address1,
            )
            self.a_transit_from_to(
                50,
                datetime(2021, 1, 1, 0, 6).astimezone(pytz.utc),
                datetime(2021, 1, 1, 0, 10).astimezone(pytz.utc),
                client,
                driver,
                address1,
                address2,
            )
            self.a_transit_from_to(
                50,
                datetime(2021, 1, 1, 0, 15).astimezone(pytz.utc),
                datetime(2021, 1, 1, 0, 20).astimezone(pytz.utc),
                client,
                driver,
                address2,
                address3,
            )
            # 3-2-1
            self.a_transit_from_to(
                50,
                datetime(2021, 1, 2, 0, 00).astimezone(pytz.utc),
                datetime(2021, 1, 2, 0, 10).astimezone(pytz.utc),
                client,
                driver,
                address3,
                address2,
            )
            self.a_transit_from_to(
                50,
                datetime(2021, 1, 2, 0, 15).astimezone(pytz.utc),
                datetime(2021, 1, 2, 0, 20).astimezone(pytz.utc),
                client,
                driver,
                address2,
                address1,
            )
            # 1-5
            self.a_transit_from_to(
                50,
                datetime(2021, 1, 3, 0, 00).astimezone(pytz.utc),
                datetime(2021, 1, 3, 0, 10).astimezone(pytz.utc),
                client,
                driver,
                address1,
                address5,
            )
            # 3-1-2-5-4-5
            self.a_transit_from_to(
                50,
                datetime(2021, 2, 1, 0, 00).astimezone(pytz.utc),
                datetime(2021, 2, 1, 0, 10).astimezone(pytz.utc),
                client,
                driver,
                address3,
                address1,
            )
            self.a_transit_from_to(
                50,
                datetime(2021, 2, 1, 0, 20).astimezone(pytz.utc),
                datetime(2021, 2, 1, 0, 25).astimezone(pytz.utc),
                client,
                driver,
                address1,
                address2,
            )
            self.a_transit_from_to(
                50,
                datetime(2021, 2, 1, 0, 30).astimezone(pytz.utc),
                datetime(2021, 2, 1, 0, 35).astimezone(pytz.utc),
                client,
                driver,
                address2,
                address5,
            )
            self.a_transit_from_to(
                50,
                datetime(2021, 2, 1, 0, 40).astimezone(pytz.utc),
                datetime(2021, 2, 1, 0, 45).astimezone(pytz.utc),
                client,
                driver,
                address5,
                address4,
            )
            self.a_transit_from_to(
                50,
                datetime(2021, 2, 1, 0, 50).astimezone(pytz.utc),
                datetime(2021, 2, 1, 0, 55).astimezone(pytz.utc),
                client,
                driver,
                address4,
                address5,
            )

            # when
            analyzed_addresses_dto: AnalyzedAddressesDTO = self.transit_analyzer_controller.analyze(
                client.id,
                address5.id
            )

            # then
            # 5-1-2-3
            self.addresses_contain_exactly(analyzed_addresses_dto, (address5, address1, address2, address3))

    # pytanie za 100 punktów, czy ten test będzie działał na grafie, bo tam jest warunek na ścieżkę o długości
    # przynajmniej 1...
    @pytest.mark.skip(reason="disabled")
    async def test_can_find_long_travel_between_others(self):
        # given
        client: Client = self.fixtures.a_client()
        # and
        driver: Driver = self.fixtures.a_nearby_driver_default("WA001", 1, 1, CarType.CarClass.VAN, datetime.now())
        # and
        with freeze_time(datetime(2021, 1, 1, 0, 0).astimezone(pytz.utc)):
            address1: Address = Address(country="5_1", district="1", city="1", street="1", building_number=1)
            address2: Address = Address(country="5_2", district="2", city="2", street="2", building_number=2)
            address3: Address = Address(country="5_3", district="3", city="3", street="3", building_number=3)
            address4: Address = Address(country="5_4", district="4", city="4", street="4", building_number=3)
            address5: Address = Address(country="5_5", district="5", city="5", street="5", building_number=3)
            # and
            # 1-2-3
            self.a_transit_from_to(
                50,
                datetime(2021, 1, 1, 0, 0).astimezone(pytz.utc),
                datetime(2021, 1, 1, 0, 5).astimezone(pytz.utc),
                client,
                driver,
                address1,
                address2,
            )
            self.a_transit_from_to(
                50,
                datetime(2021, 1, 1, 0, 10).astimezone(pytz.utc),
                datetime(2021, 1, 1, 0, 15).astimezone(pytz.utc),
                client,
                driver,
                address2,
                address3,
            )
            # 4-5
            self.a_transit_from_to(
                50,
                datetime(2021, 1, 1, 0, 20).astimezone(pytz.utc),
                datetime(2021, 1, 1, 0, 25).astimezone(pytz.utc),
                client,
                driver,
                address4,
                address5,
            )

            # when
            analyzed_addresses_dto: AnalyzedAddressesDTO = self.transit_analyzer_controller.analyze(
                client.id,
                address1.id
            )

            # then
            # 1-2
            self.addresses_contain_exactly(analyzed_addresses_dto, (address1, address2, address3))

    def a_transit_from_to(
        self,
        published_at: datetime,
        completed_at: datetime,
        client: Client,
        pickup: Address,
        destination: Address,
    ) -> None:
        when(self.geocoding_service.geocode_address(destination)).thenReturn([1.0, 1.0])
        driver: Driver = self.fixtures.a_random_nearby_driver(self.geocoding_service, pickup)
        self.fixtures.a_journey_with_fixed_clock(
            40, published_at, completed_at, client, driver, pickup, destination,)

    def addresses_contain_exactly(
        self,
        analyzed_addresses_dto: AnalyzedAddressesDTO,
        expected_addresses: Iterable[Address],
    ):
        expected_hashes = tuple([address.hash for address in expected_addresses])
        self.assertTrue(expected_hashes == self.hashes_of_addresses(analyzed_addresses_dto))

    def hashes_of_addresses(self, analyzed_addresses_dto) -> Tuple[int]:
        return tuple([int(address.hash) for address in analyzed_addresses_dto.addresses])

    def tearDown(self) -> None:
        drop_db_and_tables()
