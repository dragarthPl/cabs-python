from typing import Optional

from entity import Driver
from pydantic import BaseModel


class DriverDTO(BaseModel):
    id: Optional[int]
    first_name: Optional[str]
    last_name: Optional[str]
    driver_license: Optional[str]
    photo: Optional[str]
    status: Optional[Driver.Status]
    type: Optional[Driver.Type]
