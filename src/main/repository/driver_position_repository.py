from datetime import datetime
from typing import List, Optional

from core.database import get_session
from dto.driver_position_dtov_2 import DriverPositionDTOV2
from entity import Driver
from entity.driver_position import DriverPosition
from fastapi import Depends
from sqlalchemy import text
from sqlmodel import Session


class DriverPositionRepositoryImp:
    session: Session

    def __init__(self, session: Session = Depends(get_session)):
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
            DriverPosition.seen_at
        ).asc().all()

    def find_average_driver_position_since(
            self, latitude_min, latitude_max, longitude_min, longitude_max, date: datetime) -> List[DriverPositionDTOV2]:
        stmt = text(
            "SELECT new io.legacyfighter.cabs.dto.DriverPositionDTOV2("
            "p.driver,"
            " avg(p.latitude), "
            "avg(p.longitude),"
            " max(p.seenAt)) "
            "FROM DriverPosition p where p.latitude between :latitude_min "
            "and :latitude_max and p.longitude between :longitude_min and :longitude_max and"
            " p.seenAt >= :date group by p.driver.id")
        stmt = stmt.columns(
            DriverPositionDTOV2.driver,
            DriverPositionDTOV2.latitude,
            DriverPositionDTOV2.longitude,
            DriverPositionDTOV2.seen_at
        )
        return self.session.query(DriverPositionDTOV2).from_statement(stmt).params(
            latitude_min=latitude_min,
            latitude_max=latitude_max,
            longitude_min=longitude_min,
            longitude_max=longitude_max,
            date=date
        ).all()
