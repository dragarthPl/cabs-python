from fastapi import Depends
from fastapi_utils.cbv import cbv
from fastapi_utils.inferring_router import InferringRouter

from dto.claim_dto import ClaimDTO
from entity.claim import Claim
from service.claim_service import ClaimService

claim_router = InferringRouter()

@cbv(claim_router)
class ClaimController:

    claim_service: ClaimService = Depends(ClaimService)

    @claim_router.post("/claims/createDraft")
    def create(self, claim_dto: ClaimDTO) -> ClaimDTO:
        created: Claim = self.claim_service.create(claim_dto)
        return self.to_dto(created)
