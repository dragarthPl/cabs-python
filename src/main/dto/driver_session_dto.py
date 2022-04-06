from datetime import datetime
from typing import Optional

from entity import CarType
from pydantic import BaseModel


class DriverSessionDTO(BaseModel):
    logged_at: Optional[datetime]
    logged_out_at: Optional[datetime]
    plates_number: Optional[str]
    car_class: Optional[CarType.CarClass]
    car_brand: Optional[str]
