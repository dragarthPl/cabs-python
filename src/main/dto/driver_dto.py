from typing import Optional, Any

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

    def __init__(self, *, driver: Driver = None, **data: Any):
        if driver is not None:
            data.update(**driver.dict())
        super().__init__(**data)
        if driver is not None and driver.get_driver_license():
            self.driver_license = driver.get_driver_license().as_string()
