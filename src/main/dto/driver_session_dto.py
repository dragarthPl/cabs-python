import hashlib
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

    def __hash__(self):
        m = hashlib.md5()
        for s in (
                self.logged_at,
                self.logged_out_at,
                self.plates_number,
                self.car_class,
                self.car_brand,
        ):
            m.update(str(s).encode('utf-8'))
        return int(m.hexdigest(), 16)
