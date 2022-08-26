from typing import Optional

from fastapi import Depends
from sqlmodel import Session

from core.database import get_session
from transitdetails.transit_details import TransitDetails


class TransitDetailsRepository:
    session: Session

    def __init__(self, session: Session = Depends(get_session)):
        self.session = session

    def find_by_transit_id(self, transit_id: int) -> Optional[TransitDetails]:
        return self.session.query(TransitDetails).where(TransitDetails.transit_id == transit_id).first()

    def save(self, transit_details: TransitDetails) -> Optional[TransitDetails]:
        self.session.add(transit_details)
        self.session.commit()
        self.session.refresh(transit_details)
        return transit_details
