from typing import Optional

from fastapi import Depends
from sqlalchemy import func
from sqlmodel import Session, select

from core.database import get_session
from entity.claim import Claim


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

    