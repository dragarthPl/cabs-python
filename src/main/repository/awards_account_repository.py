from typing import Optional, List

from core.database import get_session
from entity import Client, AwardedMiles
from entity.miles.awards_account import AwardsAccount
from fastapi import Depends
from sqlmodel import Session


class AwardsAccountRepositoryImp:
    session: Session

    def __init__(self, session: Session = Depends(get_session)):
        self.session = session

    def find_by_client(self, client: Client) -> AwardsAccount:
        statement = self.session.query(AwardsAccount).where(AwardsAccount.client_id == client.id)
        results = self.session.exec(statement)
        return results.scalar_one_or_none()

    def find_all_miles_by(self, client: Client) -> List[AwardedMiles]:
        return self.find_by_client(client).get_miles()

    def save(self, awards_account: AwardsAccount) -> Optional[AwardsAccount]:
        self.session.add(awards_account)
        self.session.commit()
        self.session.refresh(awards_account)
        return awards_account
