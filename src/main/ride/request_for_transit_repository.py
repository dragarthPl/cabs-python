from typing import Optional
from uuid import UUID

from injector import inject
from sqlmodel import Session

from ride.request_for_transit import RequestForTransit


class RequestForTransitRepository:
    session: Session

    @inject
    def __init__(self, session: Session):
        self.session = session

    def find_by_request_uuid(self, request_uuid: UUID) -> Optional[RequestForTransit]:
        return self.session.query(RequestForTransit).where(RequestForTransit.request_uuid == request_uuid).first()

    def save(self, request_for_transit: RequestForTransit) -> Optional[RequestForTransit]:
        self.session.add(request_for_transit)
        self.session.commit()
        self.session.refresh(request_for_transit)
        return request_for_transit

    def get_one(self, request_id: int) -> Optional[RequestForTransit]:
        return self.session.query(RequestForTransit).where(RequestForTransit.id == request_id).first()
