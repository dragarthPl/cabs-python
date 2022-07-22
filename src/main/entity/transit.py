from __future__ import annotations

import calendar
import enum
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal
from typing import Optional, Set, Any

import pytz
from dateutil.relativedelta import relativedelta
from dateutil.tz import tzlocal

from zoneinfo import ZoneInfo

from common.base_entity import BaseEntity
from distance.distance import Distance
from entity import Address, CarType, Tariff
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
    tariff_km_rate: Optional[float] = 0
    tariff_name: Optional[str] = None
    tariff_base_fee: Optional[int] = 0

    km: Optional[float] = Field(default=0.0, sa_column=Column(Float))

    price: Optional[int] = 0
    estimated_price: Optional[int] = 0
    drivers_fee: Optional[int] = 0

    date_time: Optional[datetime] = Field(default=None, sa_column=Column(DateTime, nullable=True))

    published: Optional[datetime] = Field(default=None, sa_column=Column(DateTime, nullable=True))

    # @OneToOne
    client_id: Optional[int] = Field(default=None, foreign_key="client.id")
    client: Optional['Client'] = Relationship(
        sa_relationship=relationship(
            "entity.client.Client",
            backref=backref("transit"))
    )
    car_type: Optional[CarType.CarClass] = Field(sa_column=Column(Enum(CarType.CarClass)))
    complete_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime, nullable=True))

    def __init__(self, **data: Any):
        tariff: Optional[Tariff] = None
        km: Optional[Distance] = None
        status: Optional[Transit.Status] = None
        if "tariff" in data:
            tariff = data.pop("tariff")
        if "km" in data:
            km = data.pop("km")
        if "status" in data:
            status = data.pop("status")
        super().__init__(**data)
        self.status = status
        if data.get("price"):
            self.set_price(data["price"])
        if data.get("estimated_price"):
            self.set_estimated_price(data["estimated_price"])
        if data.get("drivers_fee"):
            self.set_price(data["drivers_fee"])
        if data.get("distance"):
            self.km = data["distance"].to_km_in_float()
        if data.get("client"):
            self.client_id = data["client"].id
            self.client = data["client"]
        if tariff:
            self.tariff_name = tariff.name
            self.tariff_base_fee = tariff.base_fee
            self.tariff_km_rate = tariff.km_rate
        if km:
            self.km = km.to_km_in_float()
        if data.get("date_time", None):
            self.set_date_time(data.get("date_time", None))
        if data.get("car_class"):
            self.car_type = data["car_class"]

    def change_pickup_to(
            self,
            new_address: Address,
            new_distance: Distance,
            distance_from_previous_pickup: float
    ) -> None:
        if distance_from_previous_pickup > 0.25:
            raise AttributeError("Address 'from' cannot be changed, id = " + str(self.id))
        if self.status != Transit.Status.DRAFT and self.status != Transit.Status.WAITING_FOR_DRIVER_ASSIGNMENT:
            raise AttributeError("Address 'from' cannot be changed, id = " + str(self.id))
        elif self.pickup_address_change_counter > 2:
            raise AttributeError("Address 'from' cannot be changed, id = " + str(self.id))
        self.address_from = new_address
        self.pickup_address_change_counter = self.pickup_address_change_counter + 1
        self.km = new_distance.to_km_in_float()
        self.estimate_cost()

    def change_destination_to(self, new_address: Address, new_distance: Distance) -> None:
        if self.status == Transit.Status.COMPLETED:
            raise AttributeError("Address 'to' cannot be changed, id = " + str(self.id))

        self.address_to = new_address
        self.km = new_distance.to_km_in_float()
        self.estimate_cost()

    def cancel(self) -> None:
        if self.status not in (
            Transit.Status.DRAFT,
            Transit.Status.WAITING_FOR_DRIVER_ASSIGNMENT,
            Transit.Status.TRANSIT_TO_PASSENGER
        ):
            raise AttributeError("Transit cannot be canceled, id = " + str(self.id))

        self.status = Transit.Status.CANCELLED
        self.driver = None
        self.km = Distance.ZERO.to_km_in_float()
        self.awaiting_drivers_responses = 0

    def can_propose_to(self, driver: Driver) -> bool:
        return driver not in self.drivers_rejections

    def propose_to(self, driver: Driver) -> None:
        if self.can_propose_to(driver):
            self.proposed_drivers.append(driver)
            self.awaiting_drivers_responses = self.awaiting_drivers_responses + 1

    def fail_driver_assignment(self) -> None:
        self.status = Transit.Status.DRIVER_ASSIGNMENT_FAILED
        self.driver = None
        self.km = Distance.ZERO.to_km_in_float()
        self.awaiting_drivers_responses = 0

    def should_not_wait_for_driver_any_more(self, when: datetime) -> bool:
        return self.status == Transit.Status.CANCELLED or self.published + relativedelta(seconds=300) < when

    def accept_by(self, driver: Driver, when: datetime) -> None:
        if self.driver != None:
            raise AttributeError("Transit already accepted, id = " + str(self.id))
        else:
            if driver not in self.proposed_drivers:
                raise AttributeError("Driver out of possible drivers, id = " + str(self.id))
            else:
                if driver in self.drivers_rejections:
                    raise AttributeError("Driver out of possible drivers, id = " + str(self.id))
            self.driver = driver
            self.driver.is_occupied = True
            self.awaiting_drivers_responses = 0
            self.accepted_at = when
            self.status = Transit.Status.TRANSIT_TO_PASSENGER

    def start(self, when: datetime) -> None:
        if self.status != Transit.Status.TRANSIT_TO_PASSENGER:
            raise AttributeError("Transit cannot be started, id = " + str(self.id))
        self.started = when
        self.status = Transit.Status.IN_TRANSIT

    def reject_by(self, driver: Driver) -> None:
        self.drivers_rejections.append(driver)
        self.awaiting_drivers_responses = self.awaiting_drivers_responses - 1

    def publish_at(self, when: datetime) -> None:
        self.status = Transit.Status.WAITING_FOR_DRIVER_ASSIGNMENT
        self.published = when

    def complete_ride_at(self, when: datetime, destination_address: Address, distance: Distance) -> None:
        if self.status == Transit.Status.IN_TRANSIT:
            self.km = distance.to_km_in_float()
            self.estimate_cost()
            self.complete_at = when
            self.address_to = destination_address
            self.status = Transit.Status.COMPLETED
            self.calculate_final_costs()
        else:
            raise AttributeError("Cannot complete Transit, id = " + str(self.id))

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
        money: Money = self.get_tariff().calculate_cost(Distance.of_km(self.km))
        self.price = money.value
        return money

    def get_km(self) -> Distance:
        return Distance.of_km(self.km)

    def get_tariff(self) -> Tariff:
        return Tariff(km_rate=self.tariff_km_rate, base_fee=self.tariff_base_fee, name=self.tariff_name)

    def set_tariff(self, tariff: Tariff) -> None:
        self.tariff_name = tariff.name
        self.tariff_base_fee = tariff.base_fee
        self.tariff_km_rate = tariff.km_rate

    def get_price(self) -> Money:
        return Money(self.price)

    def set_price(self, price: Money) -> None:
        self.price = price.value

    def get_estimated_price(self) -> Money:
        return Money(self.estimated_price)

    def set_estimated_price(self, estimated_price: Money) -> None:
        self.estimated_price = estimated_price.value

    def get_date_time(self) -> datetime:
        return self.date_time

    def set_date_time(self, date_time: datetime) -> None:
        self.set_tariff(Tariff.of_time(date_time.astimezone(tzlocal())))
        self.date_time = date_time

    def get_drivers_fee(self) -> Money:
        return Money(self.drivers_fee)

    def set_drivers_fee(self, drivers_fee: Money) -> None:
        self.drivers_fee = drivers_fee.value

    def __eq__(self, o):
        if not isinstance(o, Transit):
            return False
        return self.id is not None and self.id == o.id
