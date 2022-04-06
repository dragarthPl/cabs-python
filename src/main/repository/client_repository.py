from fastapi import Depends
from sqlmodel import Session, select

from core.database import get_session
from entity import Client


class ClientRepositoryImp:
    session: Session

    def __init__(self, session: Session = Depends(get_session)):
        self.session = session

    def get_one(self, client_id: int) -> Client:
        statement = select(Client).where(Client.id == client_id)
        results = self.session.exec(statement)
        return results.first()
