from typing import Optional

from core.database import get_session
from entity import DriverAttribute
from fastapi import Depends
from sqlmodel import Session


class DriverAttributeRepositoryImp:
    session: Session

    def __init__(self, session: Session = Depends(get_session)):
        self.session = session

    def save(self, driver_attribute: DriverAttribute) -> Optional[DriverAttribute]:
        self.session.add(driver_attribute)
        self.session.commit()
        self.session.refresh(driver_attribute)
        return driver_attribute
