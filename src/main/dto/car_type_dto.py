from typing import Any, Type, Optional

from pydantic import BaseModel

from entity.car_type import CarType


class CarTypeDTO(BaseModel):
    id: Optional[int]
    car_class: CarType.CarClass
    status: CarType.Status
    cars_counter: int = 0
    description: str
    active_cars_counter: int = 0
    min_no_of_cars_to_activate_class: int = 0


