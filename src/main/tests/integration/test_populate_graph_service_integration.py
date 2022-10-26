from typing import List
from unittest import TestCase

from fastapi_events import middleware_identifier
from mockito import when

from cabs_application import CabsApplication
from core.database import create_db_and_tables, drop_db_and_tables
from entity import Client, Address
from geolocation.geocoding_service import GeocodingService
from crm.transitanalyzer.graph_transit_analyzer import GraphTransitAnalyzer
from crm.transitanalyzer.populate_graph_service import PopulateGraphService

from tests.common.fixtures import DependencyResolver, Fixtures

dependency_resolver = DependencyResolver()

class TestPopulateGraphServiceIntegration(TestCase):
    fixtures: Fixtures = dependency_resolver.resolve_dependency(Fixtures)
    populate_graph_service: PopulateGraphService = dependency_resolver.resolve_dependency(PopulateGraphService)
    analyzer: GraphTransitAnalyzer = dependency_resolver.resolve_dependency(GraphTransitAnalyzer)
    geocoding_service: GeocodingService = dependency_resolver.resolve_dependency(GeocodingService)

    async def setUp(self):
        create_db_and_tables()
        app = CabsApplication().create_app()
        middleware_identifier.set(app.middleware_stack.app._id)

    async def test_can_populate_graph_with_data_from_relational_db(self):
        # given

        client: Client = self.fixtures.a_client()
        # and

        address1: Address = Address(country="100_1",  district="1", city="1", street="1", building_number=1)
        address2: Address = Address(country="100_2",  district="2", city="2", street="2", building_number=2)
        address3: Address = Address(country="100_3",  district="3", city="3", street="3", building_number=3)
        address4: Address = Address(country="100_4",  district="4", city="4", street="4", building_number=3)
        # and
        self.a_transit_from_to(address1, address2, client)
        self.a_transit_from_to(address2, address3, client)
        self.a_transit_from_to(address3, address4, client)

        # when
        self.populate_graph_service.populate()

        # then
        result: List[int] = self.analyzer.analyze(client.id, int(address1.hash))
        self.assertTrue(result == [int(address1.hash), int(address2.hash), int(address3.hash), int(address4.hash)])

    def a_transit_from_to(self, pickup: Address, destination: Address, client: Client):
        when(self.geocoding_service).geocode_address(destination).thenReturn([1, 1])
        driver: Driver = self.fixtures.a_random_nearby_driver(self.geocoding_service, pickup)
        self.fixtures.a_journey(50, client, driver, pickup, destination)

    async def tearDown(self) -> None:
        drop_db_and_tables()
