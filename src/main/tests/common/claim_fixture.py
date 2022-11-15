from injector import inject

from crm.claims.claim import Claim
from crm.claims.claim_dto import ClaimDTO
from ride.transit_dto import TransitDTO
from crm.client import Client
from crm.claims.claim_service import ClaimService
from ride.transit import Transit
from tests.common.client_fixture import ClientFixture


class ClaimFixture:
    claim_service: ClaimService
    client_fixture: ClientFixture

    @inject
    def __init__(
        self,
        claim_service: ClaimService,
        client_fixture: ClientFixture,
    ):
        self.claim_service = claim_service
        self.client_fixture = client_fixture

    def create_claim_default_reason(self, client: Client, transit: Transit) -> Claim:
        claim_dto: ClaimDTO = self.claim_dto("Okradli mnie na hajs", "$$$", client.id, transit.id)
        claim_dto.is_draft = False
        claim: Claim = self.claim_service.create(claim_dto)
        return claim

    def create_claim(self, client: Client, transit: TransitDTO, reason: str) -> Claim:
        claim_dto: ClaimDTO = self.claim_dto("Okradli mnie na hajs", reason, client.id, transit.id)
        claim_dto.is_draft = False
        return self.claim_service.create(claim_dto)

    def create_and_resolve_claim(self, client: Client, transit: Transit) -> Claim:
        claim: Claim = self.create_claim_default_reason(client, transit)
        claim = self.claim_service.try_to_automatically_resolve(claim.id)
        return claim

    def claim_dto(self, desc: str, reason: str, client_id: int, transit_id: int) -> ClaimDTO:
        claim_dto: ClaimDTO = ClaimDTO()
        claim_dto.client_id = client_id
        claim_dto.transit_id = transit_id
        claim_dto.incident_description = desc
        claim_dto.reason = reason
        return claim_dto
