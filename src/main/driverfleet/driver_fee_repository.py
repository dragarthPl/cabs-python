from typing import Optional

from injector import inject

from sqlmodel import Session

from driverfleet.driver_fee import DriverFee


class DriverFeeRepositoryImp:
    session: Session

    @inject
    def __init__(self, session: Session):
        self.session = session

    def find_by_driver_id(self, driver_id: int) -> Optional[DriverFee]:
        return self.session.query(DriverFee).where(DriverFee.driver_id == driver_id).first()

    def save(self, driver_fee: DriverFee) -> Optional[DriverFee]:
        self.session.add(driver_fee)
        self.session.commit()
        self.session.refresh(driver_fee)
        return driver_fee
