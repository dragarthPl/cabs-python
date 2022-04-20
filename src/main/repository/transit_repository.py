from datetime import datetime
from typing import List, Optional

from sqlalchemy import desc

from core.database import get_session
from entity import Address, Client, Driver, Transit
from fastapi import Depends
from sqlmodel import Session


class TransitRepositoryImp:
    session: Session

    def __init__(self, session: Session = Depends(get_session)):
        self.session = session

    def get_one(self, transit_id: int) -> Optional[Transit]:
        return self.session.query(Transit).where(Transit.id == transit_id).first()

    def find_by_client(self, owner: Client) -> List[Transit]:
        return self.session.query(Transit).filter(Transit.client == owner).all()

    def find_all_by_driver_and_date_time_between(self, driver: Driver, from_date, to_date) -> List[Transit]:
        return self.session.query(
            Transit
        ).where(
            Transit.driver_id == driver.id
        ).filter(
            Transit.date_time >= from_date
        ).filter(
            Transit.date_time <= to_date
        ).all()

    def save(self, transit: Transit) -> Optional[Transit]:
        self.session.add(transit)
        self.session.commit()
        self.session.refresh(transit)
        return transit

    def find_all_by_client_and_from_and_status_order_by_date_time_desc(
            self, client: Client, address: Address, status: Transit.Status
    ) -> List[Transit]:
        return self.session.query(
            Transit
        ).where(
            Transit.client_id == client.id
        ).where(
            Transit.address_from_id == address.id
        ).where(
            Transit.status == status
        ).order_by(
            desc(Transit.date_time)
        ).all()

    def find_all_by_client_and_from_and_published_after_and_status_order_by_date_time_desc(
            self, client: Client, address: Address, published: datetime, status: Transit.Status
    ) -> List[Transit]:
        return self.session.query(
            Transit
        ).where(
            Transit.client_id == client.id
        ).where(
            Transit.address_from_id == address.id
        ).where(
            Transit.published > published
        ).where(
            Transit.status == status
        ).order_by(
            desc(Transit.date_time)
        ).all()
