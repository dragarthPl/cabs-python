from datetime import datetime
from typing import Optional, Any

from pydantic import BaseModel


class DriverPositionDTOV2(BaseModel):
    driver_id: Optional[int]
    latitude: Optional[float]
    longitude: Optional[float]
    seen_at: Optional[datetime]

    def __init__(self, driver_id: Optional[int], latitude: Optional[float], longitude: Optional[float],
                 seen_at: Optional[datetime], **data: Any):
        super().__init__(**data)
        self.driver_id = driver_id
        self.latitude = latitude
        self.longitude = longitude
        self.seen_at = seen_at
