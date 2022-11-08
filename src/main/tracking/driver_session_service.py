from datetime import datetime
from typing import List

from injector import inject

from carfleet.car_class import CarClass
from tracking.driver_session import DriverSession
from tracking.driver_session_repository import DriverSessionRepositoryImp
from carfleet.car_type_service import CarTypeService


class DriverSessionService:
    driver_session_repository: DriverSessionRepositoryImp
    car_type_service: CarTypeService

    @inject
    def __init__(
            self,
            driver_session_repository: DriverSessionRepositoryImp,
            car_type_service: CarTypeService
    ):
        self.driver_session_repository = driver_session_repository
        self.car_type_service = car_type_service

    def log_in(self, driver_id: int, plates_number: str, car_class: CarClass, car_brand: str) -> DriverSession:
        session = DriverSession()
        session.driver_id = driver_id
        session.logged_at = datetime.now()
        session.car_class = car_class
        session.plates_number = plates_number
        session.car_brand = car_brand
        self.car_type_service.register_active_car(session.car_class)
        return self.driver_session_repository.save(session)

    def log_out(self, session_id: int) -> None:
        session = self.driver_session_repository.get_one(session_id)
        if session is None:
            raise AttributeError("Session does not exist")
        self.car_type_service.unregister_car(session.car_class)
        session.logged_out_at = datetime.now()
        self.driver_session_repository.save(session)

    def log_out_current_session(self, driver_id: int) -> None:
        session = self.driver_session_repository.find_top_by_driver_and_logged_out_at_is_null_order_by_logged_at_desc(
            driver_id
        )
        if session != None:
            session.logged_out_at = datetime.now()
            self.car_type_service.unregister_car(session.car_class)

    def find_by_driver(self, driver_id):
        return self.driver_session_repository.find_by_driver(driver_id)

    def find_currently_logged_driver_ids(self, drivers_ids: List[int] , car_classes: List[CarClass]) -> List[int]:
        return list(map(
            lambda driver_session: driver_session.driver_id,
            self.driver_session_repository.find_all_by_logged_out_at_null_and_driver_id_in_and_car_class_in(
                drivers_ids,
                car_classes
            )
        ))
