from datetime import datetime

from fastapi import Depends

from distance.distance import Distance
from driverreport.travelleddistance.travelled_distance import TimeSlot, TravelledDistance
from driverreport.travelleddistance.travelled_distance_repository import TravelledDistanceRepository
from entity.driver_position import DriverPosition
from service.distance_calculator import DistanceCalculator


class TravelledDistanceService:
    travelled_distance_repository: TravelledDistanceRepository
    distance_calculator: DistanceCalculator

    def __init__(
        self,
        travelled_distance_repository: TravelledDistanceRepository = Depends(TravelledDistanceRepository),
        distance_calculator: DistanceCalculator = Depends(DistanceCalculator),
    ):
        self.travelled_distance_repository = travelled_distance_repository
        self.distance_calculator = distance_calculator

    def calculate_distance(self, driver_id: int, from_position: datetime, to_position: datetime) -> Distance:
        left: TimeSlot = TimeSlot.slot_that_contains(from_position)
        right: TimeSlot = TimeSlot.slot_that_contains(to_position)
        return Distance.of_km(self.travelled_distance_repository.calculate_distance(
            left.beginning,
            right.end,
            driver_id,
        ))

    def add_position(self, driver_id: int, latitude: float, longitude: float, seen_at: datetime) -> None:
        matched_slot: TravelledDistance = self.travelled_distance_repository.find_travelled_distance_time_slot_by_time(
            seen_at,
            driver_id,
        )
        now = datetime.now()
        if matched_slot:
            if matched_slot.contains(now):
                self.__add_distance_to_slot(matched_slot, latitude, longitude)
            elif matched_slot.is_before(now):
                self.__recalculate_distance_for(matched_slot, driver_id)
            self.travelled_distance_repository.save(matched_slot)
        else:

            current_time_slot: TimeSlot = TimeSlot.slot_that_contains(now)
            prev: TimeSlot = current_time_slot.prev()
            prev_travelled_distance: TravelledDistance = \
                self.travelled_distance_repository.find_travelled_distance_by_time_slot_and_driver_id(
                    prev,
                    driver_id,
                )
            if prev_travelled_distance:
                if prev_travelled_distance.ends_at(seen_at):
                    self.__add_distance_to_slot(prev_travelled_distance, latitude, longitude)
            self.__create_slot_for_now(driver_id, current_time_slot, latitude, longitude)

    def __add_distance_to_slot(self, aggregated_distance: TravelledDistance, latitude: float, longitude: float) -> None:
        travelled: Distance = Distance.of_km(self.distance_calculator.calculate_by_geo(
            latitude,
            longitude,
            aggregated_distance.last_latitude,
            aggregated_distance.last_longitude)
        )
        aggregated_distance.add_distance(travelled, latitude, longitude)

    def __recalculate_distance_for(self, aggregated_distance: TravelledDistance, driver_id: int):
        # TODO
        pass

    def __create_slot_for_now(self, driver_id: int, time_slot: TimeSlot, latitude: float, longitude: float):
        self.travelled_distance_repository.save(
            TravelledDistance(
                driver_id=driver_id, time_slot=time_slot, last_latitude=latitude, last_longitude=longitude)
        )
