from entity import CarType


class CarTypeActiveCounter:

    car_type: CarType

    def __init__(self, car_type: CarType):
        self.car_type = car_type

    def register_active_car(self):
        self.car_type.register_active_car()

    def unregister_active_car(self):
        self.car_type.unregister_active_car()

    @property
    def active_cars_counter(self) -> int:
        return self.car_type.active_cars_counter
