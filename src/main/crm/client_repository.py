from typing import Optional

from injector import inject

from crm.client import Client
from fastapi import Depends
from sqlmodel import Session, select


class ClientRepositoryImp:
    session: Session

    @inject
    def __init__(self, session: Session):
        self.session = session

    def get_one(self, client_id: int) -> Optional[Client]:
        return self.session.query(Client).where(Client.id == client_id).first()

    def save(self, client: Client) -> Optional[Client]:
        self.session.add(client)
        self.session.commit()
        self.session.refresh(client)
        return client
