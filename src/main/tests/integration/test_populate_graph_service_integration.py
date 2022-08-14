from datetime import datetime
from typing import List
from unittest import TestCase

from fastapi.params import Depends

from core.database import create_db_and_tables, drop_db_and_tables
from entity import Client, Driver, Address
from repository.transit_repository import TransitRepositoryImp
from transitanalyzer.graph_transit_analyzer import GraphTransitAnalyzer
from transitanalyzer.populate_graph_service import PopulateGraphService

from tests.common.fixtures import DependencyResolver, Fixtures

dependency_resolver = DependencyResolver()

class TestPopulateGraphServiceIntegration(TestCase):
    fixtures: Fixtures = dependency_resolver.resolve_dependency(Depends(Fixtures))
    transit_repository: TransitRepositoryImp = dependency_resolver.resolve_dependency(Depends(TransitRepositoryImp))
    populate_graph_service: PopulateGraphService = dependency_resolver.resolve_dependency(Depends(PopulateGraphService))
    analyzer: GraphTransitAnalyzer = dependency_resolver.resolve_dependency(Depends(GraphTransitAnalyzer))

    def setUp(self):
        create_db_and_tables()

    def test_can_populate_graph_with_data_from_relational_db(self):
        # given

        client: Client = self.fixtures.a_client()
        # and

        driver: Driver = self.fixtures.an_active_regular_driver()
        # and

        address1: Address = Address(country="100_1",  district="1", city="1", street="1", building_number=1)
        address2: Address = Address(country="100_2",  district="2", city="2", street="2", building_number=2)
        address3: Address = Address(country="100_3",  district="3", city="3", street="3", building_number=3)
        address4: Address = Address(country="100_4",  district="4", city="4", street="4", building_number=3)
        # and
        self.fixtures.a_requested_and_completed_transit(
            10,
            datetime.now(),
            datetime.now(), client, driver, address1, address2)
        self.fixtures.a_requested_and_completed_transit(
            10,
            datetime.now(),
            datetime.now(), client, driver, address2, address3)
        self.fixtures.a_requested_and_completed_transit(
            10,
            datetime.now(),
            datetime.now(), client, driver, address3, address4)

        # when
        self.populate_graph_service.populate()

        # then
        result: List[int] = self.analyzer.analyze(client.id, int(address1.hash))
        self.assertTrue(result == [int(address1.hash), int(address2.hash), int(address3.hash), int(address4.hash)])

    def tearDown(self) -> None:
        drop_db_and_tables()
