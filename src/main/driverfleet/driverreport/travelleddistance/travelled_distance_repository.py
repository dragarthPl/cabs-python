from datetime import datetime
from typing import Optional

from injector import inject
from sqlalchemy import text
from sqlmodel import Session
from driverfleet.driverreport.travelleddistance.travelled_distance import TravelledDistance, TimeSlot


class TravelledDistanceRepository:
    session: Session

    @inject
    def __init__(self, session: Session):
        self.session = session

    def find_travelled_distance_time_slot_by_time(self, when: datetime, driver_id: int) -> Optional[TravelledDistance]:
        stmt = text(
            "select td.interval_id, td.driver_id, td.beginning, td.end, td.last_latitude, td.last_longitude"
            " from TravelledDistance AS td"
            " where td.beginning <= :when and :when < td.end and td.driver_id = :driver_id"
        )
        return self.session.query(TravelledDistance).from_statement(stmt).params(
            when=when,
            driver_id=driver_id
        ).one_or_none()

    def find_travelled_distance_by_time_slot_and_driver_id(
        self,
        time_slot: TimeSlot,
        driver_id: int
    ) -> Optional[TravelledDistance]:
        return self.session.query(TravelledDistance).where(
            TravelledDistance.beginning == time_slot.beginning
        ).where(
            TravelledDistance.end == time_slot.end
        ).where(
            TravelledDistance.driver_id == driver_id
        ).one_or_none()

    def calculate_distance(self, beginning: datetime, to: datetime, driver_id: int) -> Optional[float]:
        stmt = text(
            "SELECT COALESCE(SUM(_inner.distance), 0) FROM "
            "((SELECT * FROM travelleddistance AS td WHERE"
            " DATETIME(td.beginning) >= DATETIME(:beginning) AND td.driver_id = :driver_id)) "
            "AS _inner WHERE DATETIME(_inner.end) <= DATETIME(:end) "
        )
        stmt = stmt.params(
            beginning=beginning,
            end=to,
            driver_id=driver_id,
        )
        result = self.session.execute(stmt).one_or_none()
        return result[0] if result else None

    def save(self, travelled_distance: TravelledDistance) -> Optional[TravelledDistance]:
        self.session.add(travelled_distance)
        self.session.commit()
        self.session.refresh(travelled_distance)
        return travelled_distance
