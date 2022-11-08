from typing import Dict, List, Optional, Any

from driverfleet.driver_attribute_dto import DriverAttributeDTO
from driverfleet.driver_attribute_name import DriverAttributeName
from driverfleet.driver_dto import DriverDTO
from tracking.driver_session_dto import DriverSessionDTO
from dto.transit_dto import TransitDTO
from pydantic import BaseModel


class DriverReport(BaseModel):
    driver_dto: Optional[DriverDTO]
    attributes: List[DriverAttributeDTO]
    sessions: Dict[DriverSessionDTO, List[TransitDTO]]

    def __init__(
            self,
            *,
            driver_dto: Optional[DriverDTO] = None,
            attributes: List[DriverAttributeDTO] = None,
            sessions: Dict[DriverSessionDTO, List[TransitDTO]] = None,
            **data: Any
    ):
        attributes = attributes or []
        sessions = sessions or {}
        data['attributes'] = attributes
        data['sessions'] = sessions
        super().__init__(**data)
        self.driver_dto = driver_dto
        self.attributes = attributes
        self.sessions = sessions

    def add_attr(self, name: DriverAttributeName, value: str):
        self.attributes.append(DriverAttributeDTO(name=name, value=value))

