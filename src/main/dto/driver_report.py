from typing import Dict, List, Optional

from dto.driver_attribute_dto import DriverAttributeDTO
from dto.driver_dto import DriverDTO
from dto.driver_session_dto import DriverSessionDTO
from dto.transit_dto import TransitDTO
from pydantic import BaseModel


class DriverReport(BaseModel):
    driver_dto: Optional[DriverDTO]
    attributes: List[DriverAttributeDTO]
    sessions: Dict[DriverSessionDTO, List[TransitDTO]]
