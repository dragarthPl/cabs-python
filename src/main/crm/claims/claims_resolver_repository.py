from typing import Optional

from injector import inject
from sqlmodel import Session

from crm.claims.claims_resolver import ClaimsResolver


class ClaimsResolverRepositoryImp:
    session: Session

    @inject
    def __init__(self, session: Session):
        self.session = session

    def save(self, claims_resolver: ClaimsResolver) -> Optional[ClaimsResolver]:
        self.session.add(claims_resolver)
        self.session.commit()
        self.session.refresh(claims_resolver)
        return claims_resolver

    def find_by_client_id(self, client_id: int):
        return self.session.query(ClaimsResolver).filter(ClaimsResolver.client_id == client_id).first()