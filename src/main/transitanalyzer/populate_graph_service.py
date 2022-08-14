from fastapi import Depends

from entity import Transit
from repository.transit_repository import TransitRepositoryImp
from transitanalyzer.graph_transit_analyzer import GraphTransitAnalyzer


class PopulateGraphService:
    transit_repository: TransitRepositoryImp
    graph_transit_analyzer: GraphTransitAnalyzer

    def __init__(
        self,
        transit_repository: TransitRepositoryImp = Depends(TransitRepositoryImp),
        graph_transit_analyzer: GraphTransitAnalyzer = Depends(GraphTransitAnalyzer),
    ):
        self.transit_repository = transit_repository
        self.graph_transit_analyzer = graph_transit_analyzer

    def populate(self):
        for transit in self.transit_repository.find_all_by_status(Transit.Status.COMPLETED):
            self.add_to_graph(transit)

    def add_to_graph(self, transit: Transit):
        client_id: int = transit.client.id
        self.graph_transit_analyzer.add_transit_between_addresses(
            client_id,
            transit.id,
            int(transit.address_from.hash),
            int(transit.address_to.hash),
            transit.started,
            transit.complete_at
        )
