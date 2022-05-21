from typing import Optional, Any

from entity import DriverAttribute
from pydantic import BaseModel


class DriverAttributeDTO(BaseModel):
    name: Optional[DriverAttribute.DriverAttributeName]
    value: Optional[str]

    def __init__(self, *, driver_attribute: DriverAttribute = None, **data: Any):
        super().__init__(**data)
        if driver_attribute:
            self.name = driver_attribute.name
            self.value = driver_attribute.value

    def __eq__(self, o):
        if o is None or not isinstance(o, DriverAttributeDTO):
            return False
        return self.name == o.name and self.value == o.value

    def __hash__(self):
        return hash((self.name, self.value))