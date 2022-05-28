from datetime import datetime

from dto.driver_position_dto import DriverPositionDTO
from entity.driver_position import DriverPosition
from fastapi import Depends
from fastapi_utils.cbv import cbv
from fastapi_utils.inferring_router import InferringRouter
from service.driver_tracking_service import DriverTrackingService

driver_tracking_router = InferringRouter(tags=["DriverTrackingController"])

@cbv(driver_tracking_router)
class DriverTrackingController:
    tracking_service: DriverTrackingService = Depends(DriverTrackingService)

    @driver_tracking_router.post("/driverPositions/")
    def create(self, driver_position_dto: DriverPositionDTO) -> DriverPositionDTO:
        driver_position = self.tracking_service.register_position(
            driver_position_dto.driver_id,
            driver_position_dto.latitude,
            driver_position_dto.longitude,
            driver_position_dto.seen_at
        )

        return self.__to_dto(driver_position)

    @driver_tracking_router.get("/driverPositions/{driver_id}/total")
    def create(self, driver_id: int, from_position: datetime, to_position: datetime) -> float:
        return self.tracking_service.calculate_travelled_distance(
            driver_id, from_position, to_position
        ).to_km_in_float()

    def __to_dto(self, driver_position: DriverPosition):
        dto = DriverPositionDTO()
        dto.driver_id = driver_position.driver.id
        dto.latitude = driver_position.latitude
        dto.longitude = driver_position.longitude
        dto.seen_at = driver_position.seen_at
        return dto
