import math
import uuid as uuid_pkg
from datetime import datetime
from typing import Any, Optional

import pytz
import sqlalchemy.types as types
from dateutil.relativedelta import relativedelta
from pydantic import BaseModel
from sqlalchemy import Column, DateTime
from sqlalchemy.orm import composite, CompositeProperty
from sqlmodel import Field, SQLModel

from distance.distance import Distance
from entity.driver_position import DriverPosition


class TimeSlot(BaseModel):
    @classmethod
    @property
    def FIVE_MINUTES(cls) -> int:
        return 300

    beginning: Optional[datetime]
    end: Optional[datetime]

    def __init__(self, beginning: datetime, end: datetime, **data: Any):
        super().__init__(**data)
        self.beginning = beginning
        self.end = end

    @staticmethod
    def of(beginning: datetime, end: datetime) -> 'TimeSlot':
        if not end > beginning:
            raise ValueError(f"From {beginning} is after to {end}")
        return TimeSlot(beginning, end)

    @classmethod
    def slot_that_contains(cls, seed: datetime) -> 'TimeSlot':
        start_of_day = seed.replace(hour=0, minute=0, second=0, microsecond=0)
        seed_date_time = seed
        seconds_from_start_of_day = (seed_date_time - start_of_day).total_seconds()
        intervals = math.floor((seconds_from_start_of_day / cls.FIVE_MINUTES))
        _from = start_of_day + relativedelta(seconds=intervals * cls.FIVE_MINUTES)
        return TimeSlot(_from, _from + relativedelta(seconds=cls.FIVE_MINUTES))

    def contains(self, timestamp: datetime) -> bool:
        return self.beginning <= timestamp < self.end

    def ends_at(self, timestamp: datetime) -> bool:
        return self.end == timestamp

    def is_before(self, timestamp: datetime) -> bool:
        return self.end < timestamp

    def prev(self) -> 'TimeSlot':
        return TimeSlot(
            self.beginning - relativedelta(seconds=self.FIVE_MINUTES),
            self.end - relativedelta(seconds=self.FIVE_MINUTES)
        )

    def to_string(self) -> str:
        return f"Slot{{beginning={self.beginning}, end={self.end}}}"

    def __str__(self) -> str:
        return self.to_string()


class TravelledDistance(SQLModel, table=True):
    __table_args__ = {'extend_existing': True}

    interval_id: uuid_pkg.UUID = Field(
        default_factory=uuid_pkg.uuid4,
        nullable=False,
        primary_key=True,
    )

    driver_id: int = Field(nullable=False)

    beginning: datetime = Field(default=datetime.now(), sa_column=Column(DateTime(timezone=True), nullable=False))
    end: datetime = Field(default=datetime.now(), sa_column=Column(DateTime(timezone=True), nullable=False))
    __time_slot: Optional[TimeSlot] = composite(TimeSlot, 'beginning', 'end')

    last_latitude: float = Field(nullable=False)

    last_longitude: float = Field(nullable=False)

    distance: float

    __distance: Distance

    class Config:
        arbitrary_types_allowed = True

    def __init__(
            self,
            *,
            driver_id: int,
            time_slot: TimeSlot,
            last_latitude: float,
            last_longitude: float,
            **data: Any
    ):
        super().__init__(**data)
        self.driver_id = driver_id
        self.beginning = time_slot.beginning
        self.end = time_slot.end
        self.last_latitude = last_latitude
        self.last_longitude = last_longitude
        self.distance = Distance.ZERO.to_km_in_float()

    def contains(self, timestamp: datetime) -> bool:
        return self.__time_slot.contains(timestamp)

    def add_distance(self, travelled: Distance, latitude: float, longitude: float) -> None:
        self.distance = self.distance + travelled.to_km_in_float()
        self.last_latitude = latitude
        self.last_longitude = longitude

    def ends_at(self, instant: datetime) -> bool:
        return self.__time_slot.ends_at(instant)

    def is_before(self, now: datetime) -> bool:
        return self.__time_slot.is_before(now)
