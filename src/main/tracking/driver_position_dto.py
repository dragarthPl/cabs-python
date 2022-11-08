from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class DriverPositionDTO(BaseModel):
    driver_id: Optional[int]
    latitude: Optional[float]
    longitude: Optional[float]
    seen_at: Optional[datetime]
