from injector import inject

from ride.transit_repository import TransitRepositoryImp
from crm.transitanalyzer.graph_transit_analyzer import GraphTransitAnalyzer
from ride.details.transit_details_dto import TransitDetailsDTO
from ride.details.transit_details_facade import TransitDetailsFacade


class PopulateGraphService:
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
        for transit in self.transit_details_facade.find_completed():
            self.add_to_graph(transit)

    def add_to_graph(self, transit_details: TransitDetailsDTO):
        client_id: int = transit_details.client.id
        self.graph_transit_analyzer.add_transit_between_addresses(
            client_id,
            transit_details.transit_id,
            int(transit_details.address_from.hash),
            int(transit_details.address_to.hash),
            transit_details.started,
            transit_details.completed_at
        )
