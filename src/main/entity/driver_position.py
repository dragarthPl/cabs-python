from datetime import datetime
from typing import Optional

from common.base_entity import BaseEntity
from entity.driver import Driver
from sqlalchemy import Column, DateTime, Float
from sqlalchemy.orm import relationship
from sqlmodel import Field, Relationship


class DriverPosition(BaseEntity, table=True):
    # @ManyToOne
    driver_id: Optional[int] = Field(default=None, foreign_key="driver.id")
    driver: Optional[Driver] = Relationship(
        sa_relationship=relationship(
            "entity.driver.Driver")
    )
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