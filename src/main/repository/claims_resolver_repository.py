from typing import Optional

from sqlmodel import Session

from core.database import get_session
from fastapi import Depends

from entity import ClaimsResolver


class ClaimsResolverRepositoryImp:
    session: Session

    def __init__(self, session: Session = Depends(get_session)):
        self.session = session

    def save(self, claims_resolver: ClaimsResolver) -> Optional[ClaimsResolver]:
        self.session.add(claims_resolver)
        self.session.commit()
        self.session.refresh(claims_resolver)
        return claims_resolver

    def find_by_client_id(self, client_id: int):
        return self.session.query(ClaimsResolver).filter(ClaimsResolver.client_id == client_id).first()