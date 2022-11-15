from unittest import TestCase

from carfleet.car_class import CarClass
from core.database import create_db_and_tables, drop_db_and_tables
from carfleet.car_type_dto import CarTypeDTO
from carfleet.car_type_service import CarTypeService
from tests.common.fixtures import DependencyResolver

dependency_resolver = DependencyResolver()

class TestCarTypeUpdateIntegration(TestCase):
    car_type_service: CarTypeService = dependency_resolver.resolve_dependency(CarTypeService)

    def setUp(self):
        create_db_and_tables()

    def test_can_create_car_type(self):
        # given
        self.there_is_no_car_class_in_the_system(CarClass.VAN)

        # when
        created = self.create_car_class("duże i dobre", CarClass.VAN)

        # then
        loaded = self.load(created.id)
        self.assertEqual(CarClass.VAN, loaded.car_class)
        self.assertEqual(0, loaded.cars_counter)
        self.assertEqual(0, loaded.active_cars_counter)
        self.assertEqual("duże i dobre", loaded.description)

    def test_can_change_car_description(self):
        # given
        self.there_is_no_car_class_in_the_system(CarClass.VAN)
        # and
        self.create_car_class("duże i dobre", CarClass.VAN)

        # when
        changed = self.create_car_class("duże i bardzo dobre", CarClass.VAN)

        # then
        loaded = self.load(changed.id)
        self.assertEqual(CarClass.VAN, loaded.car_class)
        self.assertEqual(0, loaded.cars_counter)
        self.assertEqual("duże i bardzo dobre", loaded.description)

    def test_can_register_active_cars(self):
        # given
        created = self.create_car_class("duże i dobre", CarClass.VAN)
        # and
        current_active_cars_count = self.load(created.id).active_cars_counter

        # when
        self.register_active_car(CarClass.VAN)

        # then
        loaded = self.load(created.id)
        self.assertEqual(current_active_cars_count + 1, loaded.active_cars_counter)

    def test_can_unregister_active_cars(self):
        # given
        created = self.create_car_class("duże i dobre", CarClass.VAN)
        # and
        self.register_active_car(CarClass.VAN)
        # and
        current_active_cars_count = self.load(created.id).active_cars_counter

        # when
        self.unregister_active_car(CarClass.VAN)

        # then
        loaded = self.load(created.id)
        self.assertEqual(current_active_cars_count - 1, loaded.active_cars_counter)

    def register_active_car(self, car_class: CarClass):
        self.car_type_service.register_active_car(car_class)

    def unregister_active_car(self, car_class: CarClass):
        self.car_type_service.unregister_active_car(car_class)

    def load(self, car_type_id: int) -> CarTypeDTO:
        return self.car_type_service.load_dto(car_type_id)

    def create_car_class(self, desc: str, car_class: CarClass) -> CarTypeDTO:
        car_type_dto = CarTypeDTO()
        car_type_dto.car_class = car_class
        car_type_dto.description = desc
        return self.car_type_service.load_dto(self.car_type_service.create(car_type_dto).id)

    def there_is_no_car_class_in_the_system(self, car_class: CarClass):
        self.car_type_service.remove_car_type(car_class)

    def tearDown(self) -> None:
        drop_db_and_tables()
