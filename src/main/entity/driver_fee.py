from __future__ import annotations

import enum
from typing import Optional

from sqlalchemy import Column, Enum, ForeignKey, Integer
from sqlalchemy.orm import backref, relationship
from sqlmodel import Field, Relationship

from common.base_entity import BaseEntity


class DriverFee(BaseEntity, table=True):
    __table_args__ = {'extend_existing': True}

    class FeeType(enum.Enum):
        FLAT = 1
        PERCENTAGE = 2

    fee_type: FeeType = Field(sa_column=Column(Enum, nullable=False))
    # @OneToOne
    driver_id: Optional[int] = Field(default=None, foreign_key="driver.id")
    driver: Optional[Driver] = Relationship(
        sa_relationship=relationship(
            "entity.driver.Driver", back_populates="fee")
    )
    amount: Optional[int]
    min: Optional[int]

    def __eq__(self, o):
        if not isinstance(o, DriverFee):
            return False
        return self.id is not None and self.id == o.id


__all__ = ["DriverFee"]
