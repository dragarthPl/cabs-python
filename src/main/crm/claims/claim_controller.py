from typing import Optional

from fastapi_injector import Injected

from crm.claims.claim_dto import ClaimDTO
from crm.claims.claim import Claim
from fastapi_utils.cbv import cbv
from fastapi_utils.inferring_router import InferringRouter
from crm.claims.claim_service import ClaimService
from crm.claims.status import Status

claim_router = InferringRouter(tags=["ClaimController"])

@cbv(claim_router)
class ClaimController:

    claim_service: ClaimService = Injected(ClaimService)

    @claim_router.post("/claims/createDraft")
    def create(self, claim_dto: ClaimDTO) -> ClaimDTO:
        created: Claim = self.claim_service.create(claim_dto)
        return self.__to_do(created)

    @claim_router.post("/claims/send")
    def send_new(self, claim_dto: ClaimDTO) -> ClaimDTO:
        claim_dto.is_draft = False
        created: Claim = self.claim_service.create(claim_dto)
        return self.__to_do(created)

    @claim_router.post("/claims/{claim_id}/markInProcess")
    def mark_as_in_process(self, claim_id: int) -> ClaimDTO:
        claim = self.claim_service.set_status(Status.IN_PROCESS, claim_id)
        return self.__to_do(claim)

    @claim_router.get("/claims/{claim_id}}")
    def try_to_automatically_resolve(self, claim_id: int) -> ClaimDTO:
        claim = self.claim_service.try_to_automatically_resolve(claim_id)
        return self.__to_do(claim)

    def __to_do(self, claim: Claim) -> ClaimDTO:
        return ClaimDTO(**claim.dict())
