from typing import Optional

from entity import DriverAttribute
from pydantic import BaseModel


class DriverAttributeDTO(BaseModel):
    name: Optional[DriverAttribute.DriverAttributeName]
    value: Optional[str]

    def __eq__(self, o):
        if o is None or not isinstance(o, DriverAttributeDTO):
            return False
        return self.name == o.name and self.value == o.value

    def __hash__(self):
        return hash((self.name, self.value))