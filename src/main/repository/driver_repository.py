from typing import List, Optional

from core.database import get_session
from entity import Driver
from fastapi import Depends
from sqlmodel import Session


class DriverRepositoryImp:
    session: Session

    def __init__(self, session: Session = Depends(get_session)):
        self.session = session

    def save(self, driver: Driver) -> Optional[Driver]:
        self.session.add(driver)
        self.session.commit()
        self.session.refresh(driver)
        return driver

    def get_one(self, driver_id: int) -> Optional[Driver]:
        statement = self.session.query(Driver).where(Driver.id == driver_id)
        results = self.session.exec(statement)
        return results.scalar_one_or_none()
