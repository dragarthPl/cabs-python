from __future__ import annotations

from typing import Optional

from sqlalchemy import Column, Enum
from sqlalchemy.orm import relationship
from sqlmodel import Field, Relationship, SQLModel

from driverfleet.driver_attribute_name import DriverAttributeName


class DriverAttribute(SQLModel, table=True):
    __table_args__ = {'extend_existing': True}

    id: Optional[int] = Field(default=None, primary_key=True)
    name: Optional[DriverAttributeName] = Field(sa_column=Column(Enum(DriverAttributeName)))
    value: Optional[str]

    # @ManyToOne
    # @JoinColumn(name = "DRIVER_ID")
    driver_id: Optional[int] = Field(default=None, foreign_key="driver.id")
    driver: Optional[Driver] = Relationship(
        sa_relationship=relationship(
            "driverfleet.driver.Driver", back_populates="attributes")
    )

    def __init__(self, *, driver, name: DriverAttributeName, value: str, **data: Any):
        super().__init__(**data)
        self.driver = driver
        self.driver_id = driver.id
        self.name = name
        self.value = value
