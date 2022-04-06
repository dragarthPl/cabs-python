from datetime import datetime
from typing import Optional

from entity import Driver
from pydantic import BaseModel


class DriverPositionDTOV2(BaseModel):
    driver: Optional[Driver]
    latitude: Optional[float]
    longitude: Optional[float]
    seen_at: Optional[datetime]
