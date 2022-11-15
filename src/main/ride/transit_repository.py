from datetime import datetime
from typing import List, Optional
from uuid import UUID

from injector import inject
from sqlalchemy import desc, text

from crm.client import Client
from driverfleet.driver import Driver
from sqlmodel import Session

from geolocation.address.address import Address
from ride.details.status import Status
from ride.transit import Transit


class TransitRepositoryImp:
    session: Session

    @inject
    def __init__(self, session: Session):
        self.session = session

    def get_one(self, transit_id: int) -> Optional[Transit]:
        return self.session.query(Transit).where(Transit.id == transit_id).first()

    def find_by_transit_request_uuid(self, transit_request_uuid: UUID) -> Optional[Transit]:
        return self.session.query(Transit).where(Transit.transit_request_uuid == transit_request_uuid).first()

    def find_by_client_id(self, client_id: int) -> List[Transit]:
        stmt = text(
            "select T.* from transit AS T join transitdetails AS TD "
            "ON T.id = TD.transit_id where TD.client_id = :client"
        )
        return self.session.query(Transit).from_statement(stmt).params(
            client=client_id
        ).all()

    def save(self, transit: Transit) -> Optional[Transit]:
        self.session.add(transit)
        self.session.commit()
        self.session.refresh(transit)
        return transit
