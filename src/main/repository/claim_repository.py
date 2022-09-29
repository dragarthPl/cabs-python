from typing import List, Optional

from core.database import get_session
from entity import Client, Transit
from entity.claim import Claim
from fastapi import Depends
from sqlalchemy import func
from sqlmodel import Session, select


class ClaimRepositoryImp:
    session: Session

    def __init__(self, session: Session = Depends(get_session)):
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
