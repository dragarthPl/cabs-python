from datetime import datetime
from typing import List, Optional

from core.database import get_session
from entity import Driver
from entity.driver_session import DriverSession
from fastapi import Depends
from sqlmodel import Session


class DriverSessionRepositoryImp:
    session: Session

    def __init__(self, session: Session = Depends(get_session)):
        self.session = session

    def find_all_by_logged_out_at_null_and_driver_in_and_car_class_in(self, drivers, car_classes) -> List[DriverSession]:
        return self.session.query(
            DriverSession
        ).where(
            DriverSession.logged_out_at == None
        ).where(
            DriverSession.driver_id.in_(drivers)
        ).where(
            DriverSession.car_class_id.in_(car_classes)
        ).all()

    def find_all_by_driver_and_logged_at_after(self, driver: Driver, since: datetime) -> List[DriverSession]:
        return self.session.query(
            DriverSession
        ).where(DriverSession.driver_id == driver.id).where(DriverSession.logged_at > since).all()

    def save(self, driver_session: DriverSession) -> Optional[DriverSession]:
        self.session.add(driver_session)
        self.session.commit()
        self.session.refresh(driver_session)
        return driver_session

    def get_one(self, session_id) -> Optional[DriverSession]:
        return self.session.query(DriverSession).where(DriverSession.id == session_id).first()

    def find_top_by_driver_and_logged_out_at_is_null_order_by_logged_at_desc(
            self, driver: Driver) -> Optional[DriverSession]:
        return self.session.query(
            DriverSession
        ).where(
            DriverSession.driver_id == driver.id
        ).where(
            DriverSession.logged_out_at == None
        ).order_by(
            DriverSession.logged_at
        ).desc().first()

    def find_by_driver(self, driver: Driver) -> List[DriverSession]:
        return self.session.query(DriverSession).where(DriverSession.driver_id == driver.id).all()

