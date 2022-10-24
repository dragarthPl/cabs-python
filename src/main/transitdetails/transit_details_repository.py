from datetime import datetime
from typing import Optional, List

from injector import inject
from sqlalchemy import text
from sqlmodel import Session

from core.database import get_session
from entity import Transit
from transitdetails.transit_details import TransitDetails


class TransitDetailsRepository:
    session: Session

    @inject
    def __init__(self, session: Session):
        self.session = session

    def find_by_transit_id(self, transit_id: int) -> Optional[TransitDetails]:
        return self.session.query(TransitDetails).where(TransitDetails.transit_id == transit_id).first()

    def find_by_client_id(self, client_id: int) -> List[TransitDetails]:
        return self.session.query(TransitDetails).where(TransitDetails.client_id == client_id).all()

    def find_all_by_driver_and_date_time_between(
        self,
        driver_id: int,
        since: datetime,
        to: datetime,
    ) -> List[TransitDetails]:
        stmt = text(
            "select TD.* from TransitDetails AS TD where TD.driver_id = :driver_id"
            " and TD.date_time >= :since AND "
            "date_time <= :to"
        )
        return self.session.query(TransitDetails).from_statement(stmt).params(
            driver_id=driver_id,
            since=since,
            to=to,
        ).all()

    def find_by_status(self, completed: Transit.Status) -> List[TransitDetails]:
        return self.session.query(TransitDetails).where(TransitDetails.status == completed).all()

    def save(self, transit_details: TransitDetails) -> Optional[TransitDetails]:
        self.session.add(transit_details)
        self.session.commit()
        self.session.refresh(transit_details)
        return transit_details
