from typing import Optional, Any

from carfleet.car_class import CarClass
from carfleet.car_type import CarType
from pydantic import BaseModel


class CarTypeDTO(BaseModel):
    id: Optional[int]
    car_class: Optional[CarClass]
    status: Optional[CarType.Status]
    cars_counter: Optional[int] = 0
    description: Optional[str]
    active_cars_counter: Optional[int] = 0
    min_no_of_cars_to_activate_class: Optional[int] = 0

    def __init__(self, *, active_cars_counter=0, **data: Any):
        super().__init__(**data)
        self.active_cars_counter = active_cars_counter



