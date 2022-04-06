from datetime import datetime

from common.base_entity import BaseEntity
from entity.car_type import CarType
from entity.driver import Driver


class DriverSession(BaseEntity, table=True):
    logged_at: datetime
    logged_out_at: datetime
    driver: Driver
    plates_number: str
    car_class: CarType.CarClass
    car_brand: str
