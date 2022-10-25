from datetime import datetime
from typing import List, Optional

from injector import inject
from sqlalchemy import desc

from carfleet.car_class import CarClass
from driverfleet.driver import Driver
from entity.driver_session import DriverSession
from sqlmodel import Session


class DriverSessionRepositoryImp:
    session: Session

    @inject
    def __init__(self, session: Session):
        self.session = session

    def find_all_by_logged_out_at_null_and_driver_id_in_and_car_class_in(
            self,
            driver_ids: List[int],
            car_classes: List[CarClass]
    ) -> List[DriverSession]:
        return self.session.query(
            DriverSession
        ).where(
            DriverSession.logged_out_at == None
        ).where(
            DriverSession.driver_id.in_(driver_ids)
        ).where(
            DriverSession.car_class.in_(car_classes)
        ).all()

    def find_all_by_driver_and_logged_at_after(self, driver_id: int, since: datetime) -> List[DriverSession]:
        return self.session.query(
            DriverSession
        ).where(DriverSession.driver_id == driver_id).where(DriverSession.logged_at > since).all()

    def save(self, driver_session: DriverSession) -> Optional[DriverSession]:
        self.session.add(driver_session)
        self.session.commit()
        self.session.refresh(driver_session)
        return driver_session

    def get_one(self, session_id) -> Optional[DriverSession]:
        return self.session.query(DriverSession).where(DriverSession.id == session_id).first()

    def find_top_by_driver_and_logged_out_at_is_null_order_by_logged_at_desc(
            self, driver_id: int) -> Optional[DriverSession]:
        return self.session.query(
            DriverSession
        ).where(
            DriverSession.driver_id == driver_id
        ).where(
            DriverSession.logged_out_at == None
        ).order_by(
            desc(DriverSession.logged_at)
        ).first()

    def find_by_driver(self, driver_id: int) -> List[DriverSession]:
        return self.session.query(DriverSession).where(DriverSession.driver_id == driver_id).all()

