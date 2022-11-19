from uuid import UUID

from injector import inject

from ride.request_transit_service import RequestTransitService
from ride.transit import Transit
from ride.transit_repository import TransitRepositoryImp


class StartTransitService:
    transit_repository: TransitRepositoryImp
    request_transit_service: RequestTransitService

    @inject
    def __init__(
        self,
        transit_repository: TransitRepositoryImp,
        request_transit_service: RequestTransitService,
    ):
        self.transit_repository = transit_repository
        self.request_transit_service = request_transit_service

    def start(self, request_uuid: UUID) -> Transit:
        transit: Transit = Transit(
            tariff=self.request_transit_service.find_tariff(request_uuid),
            transit_request_uuid=request_uuid
        )
        return self.transit_repository.save(transit)
