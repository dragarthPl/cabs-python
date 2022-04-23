from __future__ import annotations

import calendar
import enum
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal
from typing import Optional, Set, Any

from common.base_entity import BaseEntity
from entity import Address, CarType
from sqlalchemy import Column, Enum, Float, ForeignKey, Table, DateTime
from sqlalchemy.orm import backref, relationship
from sqlmodel import Field, Relationship, SQLModel

from money import Money


drivers_rejections_link = Table(
    'drivers_rejections_link',
    SQLModel.metadata,
    Column('transit_id', ForeignKey('transit.id')),
    Column('driver_id', ForeignKey('driver.id'))
)

proposed_drivers_link = Table(
    'proposed_drivers_link',
    SQLModel.metadata,
    Column('transit_id', ForeignKey('transit.id')),
    Column('driver_id', ForeignKey('driver.id'))
)


class Transit(BaseEntity, table=True):
    __table_args__ = {'extend_existing': True}

    class Status(enum.Enum):
        DRAFT = 1
        CANCELLED = 2
        WAITING_FOR_DRIVER_ASSIGNMENT = 3
        DRIVER_ASSIGNMENT_FAILED = 4
        TRANSIT_TO_PASSENGER = 5
        IN_TRANSIT = 6
        COMPLETED = 7

    class DriverPaymentStatus(enum.Enum):
        NOT_PAID = 1
        PAID = 2
        CLAIMED = 3
        RETURNED = 4

    class ClientPaymentStatus(enum.Enum):
        NOT_PAID = 1
        PAID = 2
        RETURNED = 3

    driver_payment_status: Optional[DriverPaymentStatus] = Field(sa_column=Column(Enum(DriverPaymentStatus)))
    client_payment_status: Optional[ClientPaymentStatus] = Field(sa_column=Column(Enum(ClientPaymentStatus)))
    payment_type: Optional['Client.PaymentType'] = Field(sa_column=Column(Enum('Client.PaymentType')))
    status: Optional[Status] = Field(sa_column=Column(Enum(Status)))
    date: Optional[datetime] = Field(default=None, sa_column=Column(DateTime, nullable=True))

    # @OneToOne
    address_from_id: Optional[int] = Field(default=None, foreign_key="address.id")
    address_from: Optional[Address] = Relationship(
        sa_relationship=relationship("Address", foreign_keys="[Transit.address_from_id]"),
    )

    # @OneToOne
    address_to_id: Optional[int] = Field(default=None, foreign_key="address.id")
    address_to: Optional[Address] = Relationship(
        sa_relationship=relationship("Address", foreign_keys="[Transit.address_to_id]"),
    )
    pickup_address_change_counter: Optional[int] = 0

    # @ManyToOne
    driver_id: Optional[int] = Field(default=None, foreign_key="driver.id")
    driver: Optional[Driver] = Relationship(
        sa_relationship=relationship(
            "entity.driver.Driver", back_populates="transits")
    )

    accepted_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime, nullable=True))
    started: Optional[datetime] = Field(default=None, sa_column=Column(DateTime, nullable=True))
    # @ManyToMany
    drivers_rejections: Set[Driver] = Relationship(
        sa_relationship=relationship(
            "entity.driver.Driver", secondary=drivers_rejections_link)
    )
    # @ManyToMany
    proposed_drivers: Set[Driver] = Relationship(
        sa_relationship=relationship(
            "entity.driver.Driver", secondary=proposed_drivers_link)
    )
    awaiting_drivers_responses: Optional[int] = 0
    factor: Optional[int] = 0
    km: Optional[float] = Field(default=0.0, sa_column=Column(Float))

    price: Optional[int] = 0
    estimated_price: Optional[int] = 0
    drivers_fee: Optional[int] = 0

    date_time: Optional[datetime] = Field(default=None, sa_column=Column(DateTime, nullable=True))

    published: Optional[datetime] = Field(default=None, sa_column=Column(DateTime, nullable=True))

    BASE_FEE: Optional[int] = 8

    # @OneToOne
    client_id: Optional[int] = Field(default=None, foreign_key="client.id")
    client: Optional['Client'] = Relationship(
        sa_relationship=relationship(
            "entity.client.Client",
            backref=backref("transit", uselist=False))
    )
    car_type: Optional[CarType.CarClass] = Field(sa_column=Column(Enum(CarType.CarClass)))
    complete_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime, nullable=True))

    def __init__(self, **data: Any):
        super().__init__(**data)
        if "price" in data:
            self.set_price(data["price"])
        if "estimated_price" in data:
            self.set_estimated_price(data["estimated_price"])
        if "drivers_fee" in data:
            self.set_price(data["drivers_fee"])

    def set_km(self, km) -> None:
        self.km = km
        self.estimate_cost()

    def estimate_cost(self) -> Money:
        if self.status == self.Status.COMPLETED:
            raise ValueError(f"Estimating cost for completed transit is forbidden, id = {self.id}")

        estimated: Money = self.__calculate_cost()

        self.set_estimated_price(estimated)
        self.price = None

        return self.get_estimated_price()

    def calculate_final_costs(self) -> Money:
        if self.status == self.Status.COMPLETED:
            return self.__calculate_cost()
        else:
            raise ValueError("Cannot calculate final cost if the transit is not completed")

    def __calculate_cost(self) -> Money:
        base_fee: int = self.BASE_FEE
        factor_to_calculate: int = self.factor
        if not factor_to_calculate:
            factor_to_calculate = 1
        km_rate: Optional[float] = None
        day: datetime = self.date_time
        # wprowadzenie nowych cennikow  od 1.01.2019
        if day.year <= 2018:
            km_rate = 1.0
            base_fee += 1
        else:

            if (day.month == 2 and day.day == 31) or (day.month == 1 and day.day == 1 and day.hour <= 6):
                km_rate = 3.50
                base_fee += 3
            else:
                # piątek i sobota po 17 do 6 następnego dnia
                if ((day.weekday() == calendar.FRIDAY and day.hour >= 17) or
                (day.weekday() == calendar.SATURDAY and day.hour <= 6) or
                (day.weekday() == calendar.SATURDAY and day.hour >= 17) or
                (day.weekday() == calendar.SUNDAY and day.hour <= 6)):
                    km_rate = 2.50
                    base_fee += 2
                else:
                    # pozostałe godziny weekendu
                    if (day.weekday() == calendar.SATURDAY and day.hour > 6 and day.hour < 17) or (day.weekday() == calendar.SUNDAY and day.hour > 6):
                        km_rate = 1.5
                    else:
                        # tydzień roboczy
                        km_rate = 1.0
                        base_fee += 1

        price_big_decimal: Decimal = Decimal(
            self.km * km_rate * factor_to_calculate + base_fee
        ).quantize(Decimal('.01'), rounding=ROUND_HALF_UP)
        final_price: Money = Money(int(str(price_big_decimal).replace(".", "")))
        self.price = final_price.value
        return final_price

    def get_price(self) -> Money:
        return Money(self.price)

    def set_price(self, price: Money) -> None:
        self.price = price.value

    def get_estimated_price(self) -> Money:
        return Money(self.estimated_price)

    def set_estimated_price(self, estimated_price: Money) -> None:
        self.estimated_price = estimated_price.value

    def get_drivers_fee(self) -> Money:
        return Money(self.drivers_fee)

    def set_drivers_fee(self, drivers_fee: Money) -> None:
        self.drivers_fee = drivers_fee.value

    def __eq__(self, o):
        if not isinstance(o, Transit):
            return False
        return self.id is not None and self.id == o.id
