from datetime import datetime
from typing import Optional, Any

from common.base_entity import BaseEntity
from driverfleet.driver import Driver
from sqlalchemy import Column, DateTime, Float, Integer
from sqlmodel import Field


class DriverPosition(BaseEntity, table=True):
    # @ManyToOne
    driver_id: Optional[int] = Field(default=0, sa_column=Column(Integer, nullable=True))
    # @Column(nullable = false)
    latitude: float = Field(sa_column=Column(Float, nullable=False))
    # @Column(nullable = false)
    longitude: float = Field(sa_column=Column(Float, nullable=False))
    # @Column(nullable = false)
    seen_at: datetime = Field(sa_column=Column(DateTime, nullable=False))

    def __eq__(self, o):
        if not isinstance(o, DriverPosition):
            return False
        return self.id is not None and self.id == o.id
