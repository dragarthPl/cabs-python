from datetime import datetime
from typing import List, Optional

from injector import inject

from driverfleet.driver import Driver
from tracking.driver_position_dtov_2 import DriverPositionDTOV2
from tracking.driver_position import DriverPosition
from sqlalchemy import text, Float, DateTime, Integer
from sqlmodel import Session


class DriverPositionRepositoryImp:
    session: Session

    @inject
    def __init__(self, session: Session):
        self.session = session

    def save(self, driver_position: DriverPosition) -> Optional[DriverPosition]:
        self.session.add(driver_position)
        self.session.commit()
        self.session.refresh(driver_position)
        return driver_position

    def find_by_driver_and_seen_at_between_order_by_seen_at_asc(
            self, driver: Driver, from_position: datetime, to_position: datetime) -> List[DriverPosition]:
        return self.session.query(DriverPosition).where(
            DriverPosition.driver_id == driver.id
        ).where(
            DriverPosition.seen_at >= from_position
        ).where(
            DriverPosition.seen_at <= to_position
        ).order_by(
            DriverPosition.seen_at.asc()
        ).all()

    def find_average_driver_position_since(
        self,
        latitude_min,
        latitude_max,
        longitude_min,
        longitude_max,
        date: datetime
    ) -> List[DriverPositionDTOV2]:
        stmt = text(
            "SELECT "
            "p.id, "
            "p.driver_id,"
            " avg(p.latitude), "
            "avg(p.longitude),"
            " max(p.seen_at) "
            "FROM driverposition as p where p.latitude between :latitude_min "
            "and :latitude_max and p.longitude between :longitude_min and :longitude_max and"
            " p.seen_at >= :date group by p.driver_id")
        stmt = stmt.columns(
            id=Integer,
            driver=Integer,
            latitude=Float,
            longitude=Float,
            seen_at=DateTime
        )
        driver_position = self.session.query(DriverPosition).from_statement(stmt).params(
            latitude_min=latitude_min,
            latitude_max=latitude_max,
            longitude_min=longitude_min,
            longitude_max=longitude_max,
            date=date
        ).all()
        return [
            DriverPositionDTOV2(
                driver_id=d.driver_id,
                latitude=d.latitude,
                longitude=d.longitude,
                seen_at=d.seen_at
            )
            for d in driver_position]
