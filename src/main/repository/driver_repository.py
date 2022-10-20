from typing import List, Optional

from injector import inject

from entity import Driver
from sqlmodel import Session


class DriverRepositoryImp:
    session: Session

    @inject
    def __init__(self, session: Session):
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
