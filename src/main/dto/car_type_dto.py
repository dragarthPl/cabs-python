from typing import Optional

from entity.car_type import CarType
from pydantic import BaseModel


class CarTypeDTO(BaseModel):
    id: Optional[int]
    car_class: Optional[CarType.CarClass]
    status: Optional[CarType.Status]
    cars_counter: Optional[int] = 0
    description: Optional[str]
    active_cars_counter: Optional[int] = 0
    min_no_of_cars_to_activate_class: Optional[int] = 0


