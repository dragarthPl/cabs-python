from datetime import datetime

from injector import inject

from entity.driver_session import DriverSession
from repository.driver_repository import DriverRepositoryImp
from repository.driver_session_repository import DriverSessionRepositoryImp
from service.car_type_service import CarTypeService


class DriverSessionService:
    driver_repository: DriverRepositoryImp
    driver_session_repository: DriverSessionRepositoryImp
    car_type_service: CarTypeService

    @inject
    def __init__(
            self,
            driver_repository: DriverRepositoryImp,
            driver_session_repository: DriverSessionRepositoryImp,
            car_type_service: CarTypeService
    ):
        self.driver_repository = driver_repository
        self.driver_session_repository = driver_session_repository
        self.car_type_service = car_type_service

    def log_in(self, driver_id, plates_number, car_class, car_brand) -> DriverSession:
        session = DriverSession()
        session.driver = self.driver_repository.get_one(driver_id)
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
            self.driver_repository.get_one(driver_id)
        )
        if session != None:
            session.logged_out_at = datetime.now()
            self.car_type_service.unregister_car(session.car_class)

    def find_by_driver(self, driver_id):
        return self.driver_session_repository.find_by_driver(self.driver_repository.get_one(driver_id))
