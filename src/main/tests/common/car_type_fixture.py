from fastapi import Depends
from injector import inject

from dto.car_type_dto import CarTypeDTO
from entity import CarType
from service.car_type_service import CarTypeService


class CarTypeFixture:

    car_type_service: CarTypeService

    @inject
    def __init__(self, car_type_service: CarTypeService):
        self.car_type_service = car_type_service

    def an_active_car_category(self, car_class: CarType.CarClass) -> CarType:
        car_type_dto: CarTypeDTO = CarTypeDTO()
        car_type_dto.car_class = car_class
        car_type_dto.description = "opis"
        car_type: CarType = self.car_type_service.create(car_type_dto)
        for _ in range(1, car_type.min_no_of_cars_to_activate_class + 1):
            self.car_type_service.register_car(car_type.car_class)
        self.car_type_service.activate(car_type.id)
        return car_type
