from __future__ import annotations
from datetime import datetime

from typing import Any, Optional
from uuid import UUID

from sqlalchemy import Column, Enum, Float, DateTime, Integer

from assignment.assignment_status import AssignmentStatus
from assignment.involved_drivers_summary import InvolvedDriversSummary
from carfleet.car_class import CarClass

from geolocation.distance import Distance
from money import Money

from sqlalchemy.orm import relationship, backref
from sqlmodel import Field, Relationship

from common.base_entity import BaseEntity
from crm.client import Client
from pricing.tariff import Tariff
from ride.details.status import Status


class TransitDetails(BaseEntity, table=True):
    __table_args__ = {'extend_existing': True}

    transit_id: Optional[int] = Field(default=0, sa_column=Column(Integer, nullable=True))
    request_uuid: UUID = Field(nullable=False)
    date_time: Optional[datetime] = Field(default=None, sa_column=Column(DateTime, nullable=True))
    complete_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime, nullable=True))

    # @OneToOne
    client_id: Optional[int] = Field(default=None, foreign_key="client.id")
    client: Optional[Client] = Relationship(
        sa_relationship=relationship("Client", backref=backref("transit_details")))

    car_type: Optional[CarClass] = Field(sa_column=Column(Enum(CarClass)))
    # @OneToOne
    address_from_id: Optional[int] = Field(default=None, foreign_key="address.id")
    address_from: Optional[Address] = Relationship(
        sa_relationship=relationship("Address", foreign_keys="[TransitDetails.address_from_id]"),
    )

    # @OneToOne
    address_to_id: Optional[int] = Field(default=None, foreign_key="address.id")
    address_to: Optional[Address] = Relationship(
        sa_relationship=relationship("Address", foreign_keys="[TransitDetails.address_to_id]"),
    )

    distance: Optional[float] = Field(default=0.0, sa_column=Column(Float))

    started: Optional[datetime] = Field(default=None, sa_column=Column(DateTime, nullable=True))
    accepted_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime, nullable=True))
    published_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime, nullable=True))

    # price: Money
    # estimated_price: Money
    # drivers_fee: Money
    price: Optional[int] = 0
    estimated_price: Optional[int] = 0
    drivers_fee: Optional[int] = 0

    driver_id: Optional[int] = Field(default=0, sa_column=Column(Integer, nullable=True))
    status: Optional[Status] = Field(sa_column=Column(Enum(Status)))
    # tariff: Tariff
    tariff_km_rate: Optional[float] = 0
    tariff_name: Optional[str] = None
    tariff_base_fee: Optional[int] = 0

    def __init__(self, **data: Any):
        tariff: Optional[Tariff] = None
        distance: Optional[Distance] = None
        estimated_price: Optional[Money] = None
        when: Optional[datetime] = None
        request_uuid: Optional[UUID] = None
        if "tariff" in data:
            tariff = data.pop("tariff")
        if "distance" in data:
            distance = data.pop("distance")
        if "estimated_price" in data:
            estimated_price = data.pop("estimated_price")
        if "when" in data:
            when = data.pop("when")
        if "request_id" in data:
            request_uuid = data.pop("request_id")
        super().__init__(**data)
        if data.get("date_time", None) or when:
            self.date_time = data.get("date_time", None) or when
        if data.get("transit_id"):
            self.transit_id = data["transit_id"]
        if data.get("address_from"):
            self.address_from = data["address_from"]
        if data.get("address_to"):
            self.address_to = data["address_to"]
        if data.get("distance"):
            self.km = data["distance"].to_km_in_float()
        if data.get("client"):
            self.client = data["client"]
        if data.get("car_class"):
            self.car_type = data["car_class"]
        self.status = Status.DRAFT
        if estimated_price:
            self.set_estimated_price(estimated_price)
        if distance:
            self.distance = distance.to_km_in_float()
        if tariff:
            self.tariff_name = tariff.name
            self.tariff_base_fee = tariff.base_fee
            self.tariff_km_rate = tariff.km_rate
        if request_uuid:
            self.request_uuid = request_uuid

    def set_estimated_price(self, estimated_price: Money) -> None:
        self.estimated_price = estimated_price.value

    def set_started_at(self, when: datetime, transit_id: int):
        self.started = when
        self.status = Status.IN_TRANSIT
        self.transit_id = transit_id

    def set_accepted_at(self, when: datetime, driver_id: int):
        self.accepted_at = when
        self.driver_id = driver_id
        self.status = Status.TRANSIT_TO_PASSENGER

    def set_published_at(self, when: datetime):
        self.published_at = when
        self.status = Status.WAITING_FOR_DRIVER_ASSIGNMENT

    def set_completed_at(self, when: datetime, price: Money, driver_fee: Money):
        self.complete_at = when
        self.price = price.value if price else None
        self.drivers_fee = driver_fee.value if driver_fee else None
        self.status = Status.COMPLETED

    def pickup_changed_to(self, new_address: Address, new_distance: Distance):
        self.address_from = new_address
        self.distance = new_distance.to_km_in_float()

    def destination_changed_to(self, new_address: Address, new_distance: Distance):
        self.address_to = new_address
        self.distance = new_distance.to_km_in_float()

    def involved_drivers_are(self, involved_drivers_summary: InvolvedDriversSummary):
        if involved_drivers_summary.status == AssignmentStatus.DRIVER_ASSIGNMENT_FAILED:
            self.status = Status.DRIVER_ASSIGNMENT_FAILED
        else:
            self.status = Status.TRANSIT_TO_PASSENGER

    def cancelled(self):
        self.status = Status.CANCELLED

    def get_price(self) -> Money:
        return Money(self.price)

    def get_estimated_price(self) -> Money:
        return Money(self.estimated_price)

    def get_drivers_fee(self) -> Money:
        return Money(self.drivers_fee)

    def get_distance(self) -> Distance:
        return Distance(self.distance)

    def get_base_fee(self) -> int:
        return self.tariff_base_fee

    def get_km_rate(self) -> float:
        return self.tariff_km_rate

    def get_tariff(self) -> Tariff:
        return Tariff(km_rate=self.tariff_km_rate, base_fee=self.tariff_base_fee, name=self.tariff_name)

    def set_tariff(self, tariff: Tariff) -> None:
        self.tariff_name = tariff.name
        self.tariff_base_fee = tariff.base_fee
        self.tariff_km_rate = tariff.km_rate
