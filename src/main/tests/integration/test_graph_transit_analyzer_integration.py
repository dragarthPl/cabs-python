from datetime import datetime
from typing import List
from unittest import TestCase

from crm.transitanalyzer.graph_transit_analyzer import GraphTransitAnalyzer
from tests.common.fixtures import DependencyResolver

dependency_resolver = DependencyResolver()


class TestGraphTransitAnalyzerIntegration(TestCase):

    analyzer: GraphTransitAnalyzer = dependency_resolver.resolve_dependency(GraphTransitAnalyzer)

    def test_can_recognize_new_address(self):
        # given
        self.analyzer.add_transit_between_addresses(1, 1, 111, 222, datetime.now(), datetime.now())
        self.analyzer.add_transit_between_addresses(1, 1, 222, 333, datetime.now(), datetime.now())
        self.analyzer.add_transit_between_addresses(1, 1, 333, 444, datetime.now(), datetime.now())

        # when
        results: List[int] = self.analyzer.analyze(1, 111)

        # then
        [self.assertIn(result, (111, 222, 333, 444)) for result in results]
