from __future__ import annotations

import enum
from typing import Optional

from sqlalchemy import Column, Enum
from sqlalchemy.orm import relationship
from sqlmodel import Field, Relationship, SQLModel


class DriverAttribute(SQLModel, table=True):
    __table_args__ = {'extend_existing': True}

    class DriverAttributeName(enum.Enum):
        PENALTY_POINTS = 1
        NATIONALITY = 2
        YEARS_OF_EXPERIENCE = 3
        MEDICAL_EXAMINATION_EXPIRATION_DATE = 4
        MEDICAL_EXAMINATION_REMARKS = 5
        EMAIL = 6
        BIRTHPLACE = 7
        COMPANY_NAME = 8

    id: Optional[int] = Field(default=None, primary_key=True)
    name: Optional[DriverAttributeName] = Field(sa_column=Column(Enum(DriverAttributeName)))
    value: Optional[str]

    # @ManyToOne
    # @JoinColumn(name = "DRIVER_ID")
    driver_id: Optional[int] = Field(default=None, foreign_key="driver.id")
    driver: Optional[Driver] = Relationship(
        sa_relationship=relationship(
            "entity.driver.Driver", back_populates="attributes")
    )
