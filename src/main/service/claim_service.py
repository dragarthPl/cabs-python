from datetime import datetime

from fastapi import Depends
from sqlmodel import Session

from config.app_properties import AppProperties, get_app_properties
from core.database import get_engine
from dto.claim_dto import ClaimDTO
from entity.claim import Claim
from repository.claim_repository import ClaimRepositoryImp
from repository.client_repository import ClientRepositoryImp
from repository.transit_repository import TransitRepositoryImp
from service.awards_service import AwardsService
from service.claim_number_generator import ClaimNumberGenerator
from sqlalchemy.future import Engine

class ClaimService:
    # clock: Clock
    engine: Engine
    client_repository: ClientRepositoryImp
    transit_repository: TransitRepositoryImp
    claim_repository: ClaimRepositoryImp
    claim_number_generator: ClaimNumberGenerator
    app_properties: AppProperties
    awards_service: AwardsService
    # client_notification_service: ClientNotificationService
    # driver_notification_service: DriverNotificationService

    def __init__(
            self,
            claim_repository: ClaimRepositoryImp = Depends(ClaimRepositoryImp),
            claim_number_generator: ClaimNumberGenerator = Depends(ClaimNumberGenerator),
            app_properties: AppProperties = Depends(get_app_properties),
            awards_service: AwardsService = Depends(AwardsService),
            engine: Engine = Depends(get_engine),
    ):
        self.claim_repository = claim_repository
        self.claim_number_generator = claim_number_generator
        self.app_properties = app_properties
        self.awards_service = awards_service
        self.engine = engine

    def create(self, claim_dto: ClaimDTO) -> Claim:
        with Session(self.engine) as session:
            claim = Claim()
            claim.creation_date = datetime.now()
            claim.claim_no = self.claim_number_generator.generate(claim)
            claim = self.update(claim_dto, claim)
            return claim

    def update(self, claim_dto: ClaimDTO, claim: Claim) -> Claim:
        client = self.client_repository.get_one(claim_dto.client_id)
        transit = self.transit_repository.get_one(claim_dto.transit_id)
        if client is None:
            raise AttributeError("Client does not exists")
        if transit is None:
            raise AttributeError("Transit does not exists")
        if claim_dto.is_draft:
            claim.status = Claim.Status.DRAFT
        else:
            claim.status = Claim.Status.NEW
        claim.owner = client
        claim.transit = transit
        claim.creation_date = datetime.now()
        claim.reason = claim_dto.reason
        claim.incident_description = claim_dto.incident_description
        return self.claim_repository.save(claim)
