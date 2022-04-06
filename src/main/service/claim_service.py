from datetime import datetime

from config.app_properties import AppProperties, get_app_properties
from core.database import get_engine
from dto.claim_dto import ClaimDTO
from entity import Client
from entity.claim import Claim
from fastapi import Depends
from repository.claim_repository import ClaimRepositoryImp
from repository.client_repository import ClientRepositoryImp
from repository.transit_repository import TransitRepositoryImp
from service.awards_service import AwardsService
from service.claim_number_generator import ClaimNumberGenerator
from service.client_notification_service import ClientNotificationService
from service.driver_notification_service import DriverNotificationService
from sqlalchemy.future import Engine
from sqlmodel import Session


class ClaimService:
    # clock: Clock
    client_repository: ClientRepositoryImp
    transit_repository: TransitRepositoryImp
    claim_repository: ClaimRepositoryImp
    claim_number_generator: ClaimNumberGenerator
    app_properties: AppProperties
    awards_service: AwardsService
    client_notification_service: ClientNotificationService
    driver_notification_service: DriverNotificationService

    def __init__(
            self,
            client_repository: ClientRepositoryImp = Depends(ClientRepositoryImp),
            transit_repository: TransitRepositoryImp = Depends(TransitRepositoryImp),
            claim_repository: ClaimRepositoryImp = Depends(ClaimRepositoryImp),
            claim_number_generator: ClaimNumberGenerator = Depends(ClaimNumberGenerator),
            app_properties: AppProperties = Depends(get_app_properties),
            awards_service: AwardsService = Depends(AwardsService),
            client_notification_service: ClientNotificationService = Depends(ClientNotificationService),
            driver_notification_service: DriverNotificationService = Depends(DriverNotificationService),
    ):
        self.client_repository = client_repository
        self.transit_repository = transit_repository
        self.claim_repository = claim_repository
        self.claim_number_generator = claim_number_generator
        self.app_properties = app_properties
        self.awards_service = awards_service
        self.client_notification_service = client_notification_service
        self.driver_notification_service = driver_notification_service

    def create(self, claim_dto: ClaimDTO) -> Claim:
        claim = Claim()
        claim.creation_date = datetime.now()
        claim.claim_no = self.claim_number_generator.generate(claim)
        claim = self.update(claim_dto, claim)
        return claim

    def find(self, claim_id: int) -> Claim:
        claim = self.claim_repository.get_one(claim_id)
        if claim is None:
            raise AttributeError("Claim does not exists")
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

    def set_status(self, new_status: Claim.Status, claim_id: int) -> Claim:
        claim = self.find(claim_id)
        claim.status = new_status
        self.claim_repository.save(claim)
        return claim

    def try_to_automatically_resolve(self, claim_id: int) -> Claim:
        claim = self.find(claim_id)
        if len(self.claim_repository.find_by_owner_and_transit(claim.owner, claim.transit)) > 1:
            claim.status = Claim.Status.ESCALATED
            claim.completion_date = datetime.now()
            claim.change_date = datetime.now()
            claim.completion_mode = Claim.CompletionMode.MANUAL
            return claim
        if len(self.claim_repository.find_by_owner(claim.owner)) <= 3:
            claim.status = Claim.Status.REFUNDED
            claim.completion_date = datetime.now()
            claim.change_date = datetime.now()
            claim.completion_mode = Claim.CompletionMode.AUTOMATIC
            self.client_notification_service.notify_client_about_refund(claim.claim_no, claim.owner.id)
            return claim
        if claim.owner.type == Client.Type.VIP:
            if claim.transit.price < self.app_properties.automatic_refund_for_vip_threshold:
                claim.status = Claim.Status.REFUNDED
                claim.completion_date = datetime.now()
                claim.change_date = datetime.now()
                claim.completion_mode = Claim.CompletionMode.AUTOMATIC
                self.client_notification_service.notify_client_about_refund(claim.claim_no, claim.owner.id)
                self.awards_service.register_special_miles(claim.owner.id, 10)
            else:
                claim.status = Claim.Status.ESCALATED
                claim.completion_date = datetime.now()
                claim.change_date = datetime.now()
                claim.completion_mode = Claim.CompletionMode.MANUAL
                self.driver_notification_service.ask_driver_for_details_about_claim(
                    claim.claim_no, claim.transit.driver.id)
        else:
            if len(self.transit_repository.find_by_client(claim.owner)) >= self.app_properties.no_of_transits_for_claim_automatic_refund:
                if claim.transit.price < self.app_properties.automatic_refund_for_vip_threshold:
                    claim.status = Claim.Status.REFUNDED
                    claim.completion_date = datetime.now()
                    claim.change_date = datetime.now()
                    claim.completion_mode = Claim.CompletionMode.AUTOMATIC
                    self.client_notification_service.notify_client_about_refund(claim.claim_no, claim.owner.id)
                else:
                    claim.status = Claim.Status.ESCALATED
                    claim.completion_date = datetime.now()
                    claim.change_date = datetime.now()
                    claim.completion_mode = Claim.CompletionMode.MANUAL
                    self.client_notification_service.ask_for_more_information(claim.claim_no, claim.owner.id)
            else:
                claim.status = Claim.Status.ESCALATED
                claim.completion_date = datetime.now()
                claim.change_date = datetime.now()
                claim.completion_mode = Claim.CompletionMode.MANUAL
                self.driver_notification_service.ask_driver_for_details_about_claim(claim.claim_no, claim.owner.id)

        return claim
