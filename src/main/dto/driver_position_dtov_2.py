from datetime import datetime
from typing import Optional, Any

from entity import Driver
from pydantic import BaseModel


class DriverPositionDTOV2(BaseModel):
    driver: Optional[Driver]
    latitude: Optional[float]
    longitude: Optional[float]
    seen_at: Optional[datetime]

    def __init__(self, driver: Optional[Driver], latitude: Optional[float], longitude: Optional[float],
                 seen_at: Optional[datetime], **data: Any):
        super().__init__(**data)
        self.driver = driver
        self.latitude = latitude
        self.longitude = longitude
        self.seen_at = seen_at
