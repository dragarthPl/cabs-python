from typing import Optional

from injector import inject

from crm.claims.claim import Claim
from sqlalchemy import func
from sqlmodel import Session


class ClaimRepositoryImp:
    session: Session

    @inject
    def __init__(self, session: Session):
        self.session = session

    def count(self):
        results = self.session.query(func.count('*')).select_from(Claim.metadata.tables["cartype"]).scalar()
        return results

    def save(self, claim: Claim) -> Optional[Claim]:
        self.session.add(claim)
        self.session.commit()
        self.session.refresh(claim)
        return claim

    def get_one(self, claim_id: int) -> Optional[Claim]:
        return self.session.query(Claim).filter(Claim.id == claim_id).first()

    def find_all_by_owner_id(self, owner_id: int):
        return self.session.query(Claim).filter(Claim.owner_id == owner_id).all()
