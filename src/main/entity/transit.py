import calendar
import enum
from datetime import datetime
from decimal import Decimal, Context, ROUND_HALF_UP
from sqlalchemy import Column, Enum, PickleType, Float
from sqlalchemy.orm import relationship, backref
from sqlmodel import Field, Relationship
from typing import Set, Optional

import pytz

from common.base_entity import BaseEntity
from entity import Address
from entity import CarType


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

    driver_payment_status: DriverPaymentStatus = Field(sa_column=Column(Enum(DriverPaymentStatus)))
    client_payment_status: ClientPaymentStatus = Field(sa_column=Column(Enum(ClientPaymentStatus)))
    payment_type: 'Client.PaymentType' = Field(sa_column=Column(Enum('Client.PaymentType')))
    status: Status = Field(sa_column=Column(Enum(Status)))
    date: datetime
    address_from_id: Optional[int] = Field(default=None, foreign_key="address.id")
    address_from: Optional[Address] = Relationship(
        sa_relationship_kwargs=dict(foreign_keys="[Transit.address_from_id]")
    )
    address_to_id: Optional[int] = Field(default=None, foreign_key="address.id")
    address_to: Optional[Address] = Relationship(
        sa_relationship_kwargs=dict(foreign_keys="[Transit.address_to_id]")
    )
    pickup_address_change_counter: int = 0
    driver: 'driver.Driver' = Field(sa_column=Column(PickleType))
    accepted_at: datetime
    started: datetime
    drivers_rejections: Set["Driver"] = Field(sa_column=Column(PickleType))
    proposed_drivers: Set["Driver"] = Field(sa_column=Column(PickleType))
    awaiting_drivers_responses: int = 0
    factor: int
    km: float = Field(default=0.0, sa_column=Column(Float))

    price: int
    estimated_price: int
    drivers_fee: int

    date_time: datetime

    published: datetime

    BASE_FEE: int = 8

    client_id: Optional[int] = Field(default=None, foreign_key="client.id")
    client: Optional['Client'] = Relationship(
        sa_relationship=relationship(
            "entity.client.Client",
            backref=backref("transit", uselist=False))
    )
    car_type: CarType.CarClass = Field(sa_column=Column(Enum(CarType.CarClass)))
    complete_at: datetime

    # @property
    # def km(self) -> float:
    #     return self._km
    #
    # @km.setter
    # def km(self, km):
    #     self._km = km
    #     self.estimate_cost()

    def estimate_cost(self) -> int:
        if self.status == self.Status.COMPLETED:
            raise ValueError(f"Estimating cost for completed transit is forbidden, id = {self.id}")

        estimated: int = self.calculate_cost()

        self.estimated_price = estimated
        self.price = None

        return self.estimated_price

    def calculate_final_costs(self) -> int:
        if self.status == self.Status.COMPLETED:
            return self.calculate_cost()
        else:
            raise ValueError("Cannot calculate final cost if the transit is not completed")

    def calculate_cost(self) -> int:
        base_fee: int = self.BASE_FEE
        factor_to_calculate: int = self.factor
        if factor_to_calculate is None:
            factor_to_calculate = 1
        km_rate: float = None
        day: datetime = datetime.now(pytz.utc)
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
                if ((day.weekday() == calendar.FRIDAY and day.hour >= 17) or (day.weekday() == calendar.SATURDAY and day.hour <= 6) or
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
            self._km * km_rate * factor_to_calculate + base_fee,
            context=Context(prec=2, rounding=ROUND_HALF_UP)
        )
        final_price: int = int(str(price_big_decimal).replace(".", ""))
        self.price = final_price
        return self.price
