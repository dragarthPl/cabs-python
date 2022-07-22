from datetime import datetime
from unittest import TestCase

import pytz
from fastapi.params import Depends
from freezegun import freeze_time
from mockito import when, ANY

from core.database import create_db_and_tables, drop_db_and_tables
from dto.analyzed_addresses_dto import AnalyzedAddressesDTO
from entity import CarType, Client, Driver, Address
from service.geocoding_service import GeocodingService
from service.transit_analyzer import TransitAnalyzer
from ui.transit_analyzer_controller import TransitAnalyzerController

from tests.common.fixtures import DependencyResolver, Fixtures

dependency_resolver = DependencyResolver()


class TestAnalyzeNearbyTransitsIntegration(TestCase):
    fixtures: Fixtures = dependency_resolver.resolve_dependency(Depends(Fixtures))

    transit_analyzer_controller: TransitAnalyzerController = TransitAnalyzerController(
        transit_analyzer=dependency_resolver.resolve_dependency(Depends(TransitAnalyzer))
    )

    geocoding_service: GeocodingService = dependency_resolver.resolve_dependency(Depends(GeocodingService))

    def setUp(self):
        create_db_and_tables()
        self.fixtures.an_active_car_category(CarType.CarClass.VAN)
        when(self.geocoding_service).geocode_address(ANY).thenReturn([1.0, 1.0])

    @freeze_time(datetime(2021, 1, 1, 0, 0).astimezone(pytz.utc))
    def test_can_find_longest_travel(self):
        # given
        client: Client = self.fixtures.a_client()
        # and
        driver: Driver = self.fixtures.a_nearby_driver("WA001")

        address1: Address = Address(country="1_1", district="1", city="1", street="1", building_number=1)
        address2: Address = Address(country="1_2", district="2", city="2", street="2", building_number=2)
        address3: Address = Address(country="1_3", district="3", city="3", street="3", building_number=3)
        address4: Address = Address(country="1_4", district="4", city="4", street="4", building_number=3)
        address5: Address = Address(country="1_5", district="5", city="5", street="5", building_number=3)
        # and
        # 1-2-3-4
        self.fixtures.a_requested_and_completed_transit(
            50,
            datetime(2021, 1, 1, 0, 00).astimezone(pytz.utc),
            datetime(2021, 1, 1, 0, 10).astimezone(pytz.utc),
            client,
            driver,
            address1,
            address2,
        )
        self.fixtures.a_requested_and_completed_transit(
            50,
            datetime(2021, 1, 1, 0, 15).astimezone(pytz.utc),
            datetime(2021, 1, 1, 0, 20).astimezone(pytz.utc),
            client,
            driver,
            address2,
            address3,
        )
        self.fixtures.a_requested_and_completed_transit(
            50,
            datetime(2021, 1, 1, 0, 25).astimezone(pytz.utc),
            datetime(2021, 1, 1, 0, 30).astimezone(pytz.utc),
            client,
            driver,
            address3,
            address4,
        )
        # 1-2-3
        self.fixtures.a_requested_and_completed_transit(
            50,
            datetime(2021, 1, 2, 0, 00).astimezone(pytz.utc),
            datetime(2021, 1, 2, 0, 10).astimezone(pytz.utc),
            client,
            driver,
            address1,
            address2,
        )
        self.fixtures.a_requested_and_completed_transit(
            50,
            datetime(2021, 1, 2, 0, 15).astimezone(pytz.utc),
            datetime(2021, 1, 2, 0, 20).astimezone(pytz.utc),
            client,
            driver,
            address2,
            address3,
        )
        # 1-3
        self.fixtures.a_requested_and_completed_transit(
            50,
            datetime(2021, 1, 3, 0, 00).astimezone(pytz.utc),
            datetime(2021, 1, 3, 0, 10).astimezone(pytz.utc),
            client,
            driver,
            address1,
            address3,
        )
        # 3-1-2-5-4-5
        self.fixtures.a_requested_and_completed_transit(
            50,
            datetime(2021, 2, 1, 0, 00).astimezone(pytz.utc),
            datetime(2021, 2, 1, 0, 10).astimezone(pytz.utc),
            client,
            driver,
            address3,
            address1,
        )
        self.fixtures.a_requested_and_completed_transit(
            50,
            datetime(2021, 2, 1, 0, 20).astimezone(pytz.utc),
            datetime(2021, 2, 1, 0, 25).astimezone(pytz.utc),
            client,
            driver,
            address1,
            address2,
        )
        self.fixtures.a_requested_and_completed_transit(
            50,
            datetime(2021, 2, 1, 0, 30).astimezone(pytz.utc),
            datetime(2021, 2, 1, 0, 35).astimezone(pytz.utc),
            client,
            driver,
            address2,
            address5,
        )
        self.fixtures.a_requested_and_completed_transit(
            50,
            datetime(2021, 2, 1, 0, 40).astimezone(pytz.utc),
            datetime(2021, 2, 1, 0, 45).astimezone(pytz.utc),
            client,
            driver,
            address5,
            address4,
        )
        self.fixtures.a_requested_and_completed_transit(
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
        hash_list = [address.hash for address in analyzed_addresses_dto.addresses]
        [
            self.assertIn(int(hash), hash_list)
            for hash in (address1.hash, address2.hash, address5.hash, address4.hash, address5.hash)
        ]

    @freeze_time(datetime(2021, 1, 1, 0, 0).astimezone(pytz.utc))
    def test_can_find_longest_travel_from_multiple_clients(self):
        # given
        client1: Client = self.fixtures.a_client()
        client2: Client = self.fixtures.a_client()
        client3: Client = self.fixtures.a_client()
        client4: Client = self.fixtures.a_client()
        # and
        driver: Driver = self.fixtures.a_nearby_driver("WA001")
        # and
        address1: Address = Address(country="2_1", district="1", city="1", street="1", building_number=1)
        address2: Address = Address(country="2_2", district="2", city="2", street="2", building_number=2)
        address3: Address = Address(country="2_3", district="3", city="3", street="3", building_number=3)
        address4: Address = Address(country="2_4", district="4", city="4", street="4", building_number=3)
        address5: Address = Address(country="2_5", district="5", city="5", street="5", building_number=3)
        # and
        # 1-2-3-4
        self.fixtures.a_requested_and_completed_transit(
            50,
            datetime(2021, 1, 1, 0, 00).astimezone(pytz.utc),
            datetime(2021, 1, 1, 0, 10).astimezone(pytz.utc),
            client1,
            driver,
            address1,
            address2,
        )
        self.fixtures.a_requested_and_completed_transit(
            50,
            datetime(2021, 1, 1, 0, 15).astimezone(pytz.utc),
            datetime(2021, 1, 1, 0, 20).astimezone(pytz.utc),
            client1,
            driver,
            address2,
            address3,
        )
        self.fixtures.a_requested_and_completed_transit(
            50,
            datetime(2021, 1, 1, 0, 25).astimezone(pytz.utc),
            datetime(2021, 1, 1, 0, 30).astimezone(pytz.utc),
            client1,
            driver,
            address3,
            address4,
        )
        # 1-2-3
        self.fixtures.a_requested_and_completed_transit(
            50,
            datetime(2021, 1, 2, 0, 00).astimezone(pytz.utc),
            datetime(2021, 1, 2, 0, 10).astimezone(pytz.utc),
            client2,
            driver,
            address1,
            address2,
        )
        self.fixtures.a_requested_and_completed_transit(
            50,
            datetime(2021, 1, 2, 0, 15).astimezone(pytz.utc),
            datetime(2021, 1, 2, 0, 20).astimezone(pytz.utc),
            client2,
            driver,
            address2,
            address3,
        )
        # 1-3
        self.fixtures.a_requested_and_completed_transit(
            50,
            datetime(2021, 1, 3, 0, 00).astimezone(pytz.utc),
            datetime(2021, 1, 3, 0, 10).astimezone(pytz.utc),
            client3,
            driver,
            address1,
            address3,
        )
        # 3-1-2-5-4-5
        self.fixtures.a_requested_and_completed_transit(
            50,
            datetime(2021, 2, 1, 0, 00).astimezone(pytz.utc),
            datetime(2021, 2, 1, 0, 10).astimezone(pytz.utc),
            client4,
            driver,
            address3,
            address1,
        )
        self.fixtures.a_requested_and_completed_transit(
            50,
            datetime(2021, 2, 1, 0, 20).astimezone(pytz.utc),
            datetime(2021, 2, 1, 0, 25).astimezone(pytz.utc),
            client4,
            driver,
            address1,
            address2,
        )
        self.fixtures.a_requested_and_completed_transit(
            50,
            datetime(2021, 2, 1, 0, 30).astimezone(pytz.utc),
            datetime(2021, 2, 1, 0, 35).astimezone(pytz.utc),
            client4,
            driver,
            address2,
            address5,
        )
        self.fixtures.a_requested_and_completed_transit(
            50,
            datetime(2021, 2, 1, 0, 40).astimezone(pytz.utc),
            datetime(2021, 2, 1, 0, 45).astimezone(pytz.utc),
            client4,
            driver,
            address5,
            address4,
        )
        self.fixtures.a_requested_and_completed_transit(
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
        hash_list = [address.hash for address in analyzed_addresses_dto.addresses]
        [
            self.assertIn(int(hash), hash_list)
            for hash in (address1.hash, address2.hash, address3.hash, address4.hash)
        ]

    @freeze_time(datetime(2021, 1, 1, 0, 0).astimezone(pytz.utc))
    def test_can_find_longest_travel_with_long_stops(self):
        # given
        client: Client = self.fixtures.a_client()
        # and
        driver: Driver = self.fixtures.a_nearby_driver("WA001")
        # and
        address1: Address = Address(country="3_1", district="1", city="1", street="1", building_number=1)
        address2: Address = Address(country="3_2", district="2", city="2", street="2", building_number=2)
        address3: Address = Address(country="3_3", district="3", city="3", street="3", building_number=3)
        address4: Address = Address(country="3_4", district="4", city="4", street="4", building_number=3)
        address5: Address = Address(country="3_5", district="5", city="5", street="5", building_number=3)
        # and
        # 1-2-3-4-(stop)-5-1
        self.fixtures.a_requested_and_completed_transit(
            50,
            datetime(2021, 2, 1, 0, 0).astimezone(pytz.utc),
            datetime(2021, 2, 1, 0, 5).astimezone(pytz.utc),
            client,
            driver,
            address1,
            address2,
        )
        self.fixtures.a_requested_and_completed_transit(
            50,
            datetime(2021, 2, 1, 0, 10).astimezone(pytz.utc),
            datetime(2021, 2, 1, 0, 15).astimezone(pytz.utc),
            client,
            driver,
            address2,
            address3,
        )
        self.fixtures.a_requested_and_completed_transit(
            50,
            datetime(2021, 2, 1, 0, 20).astimezone(pytz.utc),
            datetime(2021, 2, 1, 0, 25).astimezone(pytz.utc),
            client,
            driver,
            address3,
            address4,
        )
        self.fixtures.a_requested_and_completed_transit(
            50,
            datetime(2021, 2, 1, 1, 0).astimezone(pytz.utc),
            datetime(2021, 2, 1, 1, 10).astimezone(pytz.utc),
            client,
            driver,
            address4,
            address5,
        )
        self.fixtures.a_requested_and_completed_transit(
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
        hash_list = [address.hash for address in analyzed_addresses_dto.addresses]
        [
            self.assertIn(int(hash), hash_list)
            for hash in (address1.hash, address2.hash, address3.hash, address4.hash)
        ]

    @freeze_time(datetime(2021, 1, 1, 0, 0).astimezone(pytz.utc))
    def test_can_find_longest_travel_with_loops(self):
        # given
        client: Client = self.fixtures.a_client()
        # and
        driver: Driver = self.fixtures.a_nearby_driver("WA001")
        # and
        address1: Address = Address(country="4_1", district="1", city="1", street="1", building_number=1)
        address2: Address = Address(country="4_2", district="2", city="2", street="2", building_number=2)
        address3: Address = Address(country="4_3", district="3", city="3", street="3", building_number=3)
        address4: Address = Address(country="4_4", district="4", city="4", street="4", building_number=3)
        address5: Address = Address(country="4_5", district="5", city="5", street="5", building_number=3)
        # and
        # 5-1-2-3
        self.fixtures.a_requested_and_completed_transit(
            50,
            datetime(2021, 1, 1, 0, 00).astimezone(pytz.utc),
            datetime(2021, 1, 1, 0, 5).astimezone(pytz.utc),
            client,
            driver,
            address5,
            address1,
        )
        self.fixtures.a_requested_and_completed_transit(
            50,
            datetime(2021, 1, 1, 0, 6).astimezone(pytz.utc),
            datetime(2021, 1, 1, 0, 10).astimezone(pytz.utc),
            client,
            driver,
            address1,
            address2,
        )
        self.fixtures.a_requested_and_completed_transit(
            50,
            datetime(2021, 1, 1, 0, 15).astimezone(pytz.utc),
            datetime(2021, 1, 1, 0, 20).astimezone(pytz.utc),
            client,
            driver,
            address2,
            address3,
        )
        # 3-2-1
        self.fixtures.a_requested_and_completed_transit(
            50,
            datetime(2021, 1, 2, 0, 00).astimezone(pytz.utc),
            datetime(2021, 1, 2, 0, 10).astimezone(pytz.utc),
            client,
            driver,
            address3,
            address2,
        )
        self.fixtures.a_requested_and_completed_transit(
            50,
            datetime(2021, 1, 2, 0, 15).astimezone(pytz.utc),
            datetime(2021, 1, 2, 0, 20).astimezone(pytz.utc),
            client,
            driver,
            address2,
            address1,
        )
        # 1-5
        self.fixtures.a_requested_and_completed_transit(
            50,
            datetime(2021, 1, 3, 0, 00).astimezone(pytz.utc),
            datetime(2021, 1, 3, 0, 10).astimezone(pytz.utc),
            client,
            driver,
            address1,
            address5,
        )
        # 3-1-2-5-4-5
        self.fixtures.a_requested_and_completed_transit(
            50,
            datetime(2021, 2, 1, 0, 00).astimezone(pytz.utc),
            datetime(2021, 2, 1, 0, 10).astimezone(pytz.utc),
            client,
            driver,
            address3,
            address1,
        )
        self.fixtures.a_requested_and_completed_transit(
            50,
            datetime(2021, 2, 1, 0, 20).astimezone(pytz.utc),
            datetime(2021, 2, 1, 0, 25).astimezone(pytz.utc),
            client,
            driver,
            address1,
            address2,
        )
        self.fixtures.a_requested_and_completed_transit(
            50,
            datetime(2021, 2, 1, 0, 30).astimezone(pytz.utc),
            datetime(2021, 2, 1, 0, 35).astimezone(pytz.utc),
            client,
            driver,
            address2,
            address5,
        )
        self.fixtures.a_requested_and_completed_transit(
            50,
            datetime(2021, 2, 1, 0, 40).astimezone(pytz.utc),
            datetime(2021, 2, 1, 0, 45).astimezone(pytz.utc),
            client,
            driver,
            address5,
            address4,
        )
        self.fixtures.a_requested_and_completed_transit(
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
        hash_list = [address.hash for address in analyzed_addresses_dto.addresses]
        [
            self.assertIn(int(hash), hash_list)
            for hash in (address5.hash, address1.hash, address2.hash, address3.hash)
        ]

    # pytanie za 100 punktów, czy ten test będzie działał na grafie, bo tam jest warunek na ścieżkę o długości
    # przynajmniej 1...
    def test_can_find_long_travel_between_others(self):
        # given
        client: Client = self.fixtures.a_client()
        # and
        driver: Driver = self.fixtures.a_nearby_driver("WA001")
        # and
        address1: Address = Address(country="5_1", district="1", city="1", street="1", building_number=1)
        address2: Address = Address(country="5_2", district="2", city="2", street="2", building_number=2)
        address3: Address = Address(country="5_3", district="3", city="3", street="3", building_number=3)
        address4: Address = Address(country="5_4", district="4", city="4", street="4", building_number=3)
        address5: Address = Address(country="5_5", district="5", city="5", street="5", building_number=3)
        # and
        # 1-2-3
        self.fixtures.a_requested_and_completed_transit(
            50,
            datetime(2021, 1, 1, 0, 0).astimezone(pytz.utc),
            datetime(2021, 1, 1, 0, 5).astimezone(pytz.utc),
            client,
            driver,
            address1,
            address2,
        )
        self.fixtures.a_requested_and_completed_transit(
            50,
            datetime(2021, 1, 1, 0, 10).astimezone(pytz.utc),
            datetime(2021, 1, 1, 0, 15).astimezone(pytz.utc),
            client,
            driver,
            address2,
            address3,
        )
        # 4-5
        self.fixtures.a_requested_and_completed_transit(
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
        hash_list = [address.hash for address in analyzed_addresses_dto.addresses]
        [
            self.assertIn(int(hash), hash_list)
            for hash in (address1.hash, address2.hash, address3.hash)
        ]

    def tearDown(self) -> None:
        drop_db_and_tables()
