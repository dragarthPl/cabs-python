from uuid import UUID

from injector import inject

from ride.transit_demand import TransitDemand
from ride.transit_demand_repository import TransitDemandRepository


class DemandService:
    transit_demand_repository: TransitDemandRepository

    @inject
    def __init__(
        self,
        transit_demand_repository: TransitDemandRepository,
    ):
        self.transit_demand_repository = transit_demand_repository

    def publish_demand(self, request_uuid: UUID) -> None:
        self.transit_demand_repository.save(TransitDemand(request_uuid))

    def cancel_demand(self, request_uuid: UUID) -> None:
        transit_demand: TransitDemand = self.transit_demand_repository.find_by_transit_request_uuid(request_uuid)
        if transit_demand:
            transit_demand.cancel()

    def accept_demand(self, request_uuid: UUID) -> None:
        transit_demand: TransitDemand = self.transit_demand_repository.find_by_transit_request_uuid(request_uuid)
        if transit_demand:
            transit_demand.accept()

    def exists_for(self, request_uuid: UUID) -> bool:
        return self.transit_demand_repository.find_by_transit_request_uuid(request_uuid) is not None
