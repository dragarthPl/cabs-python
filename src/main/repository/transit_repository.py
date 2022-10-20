from datetime import datetime
from typing import List, Optional

from injector import inject
from sqlalchemy import desc, text

from entity import Address, Client, Driver, Transit
from sqlmodel import Session


class TransitRepositoryImp:
    session: Session

    @inject
    def __init__(self, session: Session):
        self.session = session

    def get_one(self, transit_id: int) -> Optional[Transit]:
        return self.session.query(Transit).where(Transit.id == transit_id).first()

    def find_all_by_status(self, status: Transit.Status) -> List[Transit]:
        return self.session.query(Transit).where(Transit.status == status).all()

    def find_by_client_id(self, client_id: int) -> List[Transit]:
        stmt = text(
            "select T.* from transit AS T join transitdetails AS TD "
            "ON T.id = TD.transit_id where TD.client_id = :client"
        )
        return self.session.query(Transit).from_statement(stmt).params(
            client=client_id
        ).all()

    def find_all_by_driver_and_date_time_between(self, driver: Driver, from_date, to_date) -> List[Transit]:
        stmt = text(
            "select T.* from transit AS T join transitdetails AS TD "
            "ON T.id = TD.transit_id where T.driver_id = :driver and TD.date_time >= :from_date AND "
            "date_time <= :to_date"
        )
        return self.session.query(Transit).from_statement(stmt).params(
            driver=driver.id,
            from_date=from_date,
            to_date=to_date,
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
