from typing import Any, Optional
from uuid import UUID

from sqlmodel import Field

from common.base_entity import BaseEntity, new_uuid
from geolocation.distance import Distance
from money import Money
from pricing.tariff import Tariff
from sqlalchemy.orm import composite


class RequestForTransit(BaseEntity, table=True):
    __table_args__ = {'extend_existing': True}

    request_uuid: UUID = Field(
        default_factory=new_uuid,
        nullable=False,
    )

    tariff_km_rate: Optional[float] = 0
    tariff_name: Optional[str] = None
    tariff_base_fee: Optional[int] = 0
    __tariff: Tariff = composite(Tariff, 'tariff_km_rate', 'tariff_name', 'tariff_base_fee')

    distance: float
    __distance: Distance = composite(Distance, 'distance')

    class Config:
        arbitrary_types_allowed = True

    def __init__(
            self,
            *,
            tariff: Tariff,
            distance: Distance,
            **data: Any
    ):
        super().__init__(**data)
        self.set_tariff(tariff)
        self.distance = distance.to_km_in_float()

    def get_estimated_price(self) -> Money:
        tariff = self.get_tariff()
        distance = self.get_distance()
        return tariff.calculate_cost(distance)

    def set_tariff(self, tariff: Tariff):
        self.tariff_km_rate = tariff.km_rate
        self.tariff_name = tariff.name
        self.tariff_base_fee = tariff.base_fee

    def get_tariff(self) -> Tariff:
        return self.__tariff

    def get_distance(self) -> Distance:
        return self.__distance
