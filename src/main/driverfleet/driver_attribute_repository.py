from typing import Optional

from injector import inject

from sqlmodel import Session

from driverfleet.driver_attribute import DriverAttribute


class DriverAttributeRepositoryImp:
    session: Session

    @inject
    def __init__(self, session: Session):
        self.session = session

    def save(self, driver_attribute: DriverAttribute) -> Optional[DriverAttribute]:
        self.session.add(driver_attribute)
        self.session.commit()
        self.session.refresh(driver_attribute)
        return driver_attribute
