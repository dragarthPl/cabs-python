from typing import Optional

from core.database import get_session
from entity import Client
from fastapi import Depends
from sqlmodel import Session, select


class ClientRepositoryImp:
    session: Session

    def __init__(self, session: Session = Depends(get_session)):
        self.session = session

    def get_one(self, client_id: int) -> Optional[Client]:
        return self.session.query(Client).where(Client.id == client_id).first()

    def save(self, client: Client) -> Optional[Client]:
        self.session.add(client)
        self.session.commit()
        self.session.refresh(client)
        return client
