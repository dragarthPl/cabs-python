from typing import List, Optional

from core.database import get_session
from entity import Driver, DriverFee
from fastapi import Depends
from sqlmodel import Session, select


class DriverFeeRepositoryImp:
    session: Session

    def __init__(self, session: Session = Depends(get_session)):
        self.session = session

    def find_by_driver(self, driver: Driver) -> Optional[DriverFee]:
        return self.session.query(DriverFee).where(DriverFee.driver_id == driver.id).first()
