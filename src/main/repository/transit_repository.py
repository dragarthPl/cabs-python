from typing import Optional

from fastapi import Depends

from core.database import get_session

from sqlmodel import Session, select

from entity.transit import Transit


class TransitRepositoryImp:
    session: Session

    def __init__(self, session: Session = Depends(get_session)):
        self.session = session

    def get_one(self, transit_id: int) -> Optional[Transit]:
        statement = select(Transit).where(Transit.id == transit_id)
        results = self.session.exec(statement)
        return results.first()
