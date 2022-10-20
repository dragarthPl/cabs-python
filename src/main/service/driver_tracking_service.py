from datetime import datetime

from injector import inject

from distance.distance import Distance
from driverreport.travelleddistance.travelled_distance_service import TravelledDistanceService
from entity import Driver
from entity.driver_position import DriverPosition
from repository.driver_position_repository import DriverPositionRepositoryImp
from repository.driver_repository import DriverRepositoryImp


class DriverTrackingService:
    position_repository: DriverPositionRepositoryImp
    driver_repository: DriverRepositoryImp
    travelled_distance_service: TravelledDistanceService

    @inject
    def __init__(
            self,
            position_repository: DriverPositionRepositoryImp,
            driver_repository: DriverRepositoryImp,
            travelled_distance_service: TravelledDistanceService
    ):
        self.position_repository = position_repository
        self.driver_repository = driver_repository
        self.travelled_distance_service = travelled_distance_service

    def register_position(self, driver_id: int, latitude: float, longitude: float, seen_at: datetime) -> DriverPosition:
        driver = self.driver_repository.get_one(driver_id)
        if driver is None:
            raise AttributeError(("Driver does not exists, id = " + str(driver_id)))
        if not driver.status == Driver.Status.ACTIVE:
            raise AttributeError(("Driver is not active, cannot register position, id = " + str(driver_id)))

        position = DriverPosition()
        position.driver = driver
        position.seen_at = seen_at
        position.latitude = latitude
        position.longitude = longitude
        position = self.position_repository.save(position)
        self.travelled_distance_service.add_position(driver_id, latitude, longitude, seen_at)
        return position

    def calculate_travelled_distance(self, driver_id: int, from_position: datetime, to_position: datetime) -> Distance:
        driver = self.driver_repository.get_one(driver_id)
        if driver is None:
            raise AttributeError(("Driver does not exists, id = " + str(driver_id)))
        return self.travelled_distance_service.calculate_distance(driver_id, from_position, to_position)
