from injector import inject

from crm.claims.claim import Claim
from crm.claims.claim_repository import ClaimRepositoryImp


class ClaimNumberGenerator:
    claim_repository: ClaimRepositoryImp

    @inject
    def __init__(
            self,
            claim_repository: ClaimRepositoryImp,
     ):
        self.claim_repository = claim_repository

    def generate(self, claim: Claim) -> str:
        count = self.claim_repository.count()
        prefix = count
        if count == 0:
            prefix = 1
        return str(count) + "---" + claim.creation_date.strftime("%d/%m/%Y")
