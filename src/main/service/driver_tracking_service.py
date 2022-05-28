from datetime import datetime

from distance.distance import Distance
from entity import Driver
from entity.driver_position import DriverPosition
from fastapi import Depends
from repository.driver_position_repository import DriverPositionRepositoryImp
from repository.driver_repository import DriverRepositoryImp
from service.distance_calculator import DistanceCalculator


class DriverTrackingService:
    position_repository: DriverPositionRepositoryImp
    driver_repository: DriverRepositoryImp
    distance_calculator: DistanceCalculator

    def __init__(
            self,
            position_repository: DriverPositionRepositoryImp = Depends(DriverPositionRepositoryImp),
            driver_repository: DriverRepositoryImp = Depends(DriverRepositoryImp),
            distance_calculator: DistanceCalculator = Depends(DistanceCalculator)
    ):
        self.position_repository = position_repository
        self.driver_repository = driver_repository
        self.distance_calculator = distance_calculator

    def register_position(self, driver_id: int, latitude: float, longitude: float) -> DriverPosition:
        driver = self.driver_repository.get_one(driver_id)
        if driver is None:
            raise AttributeError(("Driver does not exists, id = " + str(driver_id)))
        if not driver.status == Driver.Status.ACTIVE:
            raise AttributeError(("Driver is not active, cannot register position, id = " + str(driver_id)))

        position = DriverPosition()
        position.driver = driver
        position.seen_at = datetime.now()
        position.latitude = latitude
        position.longitude = longitude
        return self.position_repository.save(position)

    def calculate_travelled_distance(self, driver_id: int, from_position: datetime, to_position: datetime) -> Distance:
        driver = self.driver_repository.get_one(driver_id)
        if driver is None:
            raise AttributeError(("Driver does not exists, id = " + str(driver_id)))
        positions = self.position_repository.find_by_driver_and_seen_at_between_order_by_seen_at_asc(
            driver, from_position, to_position
        )
        distance_travelled = 0

        if len(positions) > 1:
            previous_position = positions[0]

            for position in positions[1:]:
                distance_travelled += self.distance_calculator.calculate_by_geo(
                    previous_position.latitude, previous_position.longitude,
                    position.latitude, position.longitude
                )
                previous_position = position

        return Distance.of_km(distance_travelled)
