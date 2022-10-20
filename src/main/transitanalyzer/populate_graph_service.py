from injector import inject

from entity import Transit
from repository.transit_repository import TransitRepositoryImp
from transitanalyzer.graph_transit_analyzer import GraphTransitAnalyzer
from transitdetails.transit_details_dto import TransitDetailsDTO
from transitdetails.transit_details_facade import TransitDetailsFacade


class PopulateGraphService:
    transit_repository: TransitRepositoryImp
    graph_transit_analyzer: GraphTransitAnalyzer
    transit_details_facade: TransitDetailsFacade

    @inject
    def __init__(
        self,
        transit_repository: TransitRepositoryImp,
        graph_transit_analyzer: GraphTransitAnalyzer,
        transit_details_facade: TransitDetailsFacade,
    ):
        self.transit_repository = transit_repository
        self.graph_transit_analyzer = graph_transit_analyzer
        self.transit_details_facade = transit_details_facade

    def populate(self):
        for transit in self.transit_repository.find_all_by_status(Transit.Status.COMPLETED):
            self.add_to_graph(transit)

    def add_to_graph(self, transit: Transit):
        transit_details: TransitDetailsDTO = self.transit_details_facade.find(transit.id)
        client_id: int = transit_details.client.id
        self.graph_transit_analyzer.add_transit_between_addresses(
            client_id,
            transit.id,
            int(transit_details.address_from.hash),
            int(transit_details.address_to.hash),
            transit_details.started,
            transit_details.completed_at
        )
