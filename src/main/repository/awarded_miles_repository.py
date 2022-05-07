from typing import List, Optional

from core.database import get_session
from entity import AwardedMiles, Client
from fastapi import Depends
from sqlmodel import Session


class AwardedMilesRepositoryImp:
    session: Session

    def __init__(self, session: Session = Depends(get_session)):
        self.session = session

    def find_all_by_client(self, client: Client) -> List[AwardedMiles]:
        return self.session.query(AwardedMiles).where(AwardedMiles.client_id == client.id).all()

    def save(self, awarded_miles: AwardedMiles) -> Optional[AwardedMiles]:
        self.session.add(awarded_miles)
        self.session.commit()
        self.session.refresh(awarded_miles)
        return awarded_miles
