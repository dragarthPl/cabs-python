from typing import Optional
from uuid import UUID

from injector import inject
from sqlmodel import Session

from ride.transit_demand import TransitDemand


class TransitDemandRepository:
    session: Session

    @inject
    def __init__(self, session: Session):
        self.session = session

    def find_by_transit_request_uuid(self, request_uuid: UUID) -> TransitDemand:
        return self.session.query(TransitDemand).where(TransitDemand.transit_request_uuid == request_uuid).first()

    def save(self, transit_demand: TransitDemand) -> Optional[TransitDemand]:
        self.session.add(transit_demand)
        self.session.commit()
        self.session.refresh(transit_demand)
        return transit_demand
