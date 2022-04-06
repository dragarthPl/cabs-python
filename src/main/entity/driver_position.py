from datetime import datetime

from common.base_entity import BaseEntity
from entity.driver import Driver


class DriverPosition(BaseEntity, table=True):
    driver: Driver
    latitude: float
    longitude: float
    seen_at: datetime
