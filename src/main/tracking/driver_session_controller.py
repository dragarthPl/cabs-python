from typing import List

from fastapi_injector import Injected

from tracking.driver_session_dto import DriverSessionDTO
from fastapi_utils.cbv import cbv
from fastapi_utils.inferring_router import InferringRouter
from tracking.driver_session_service import DriverSessionService

driver_session_router = InferringRouter(tags=["DriverSessionController"])

@cbv(driver_session_router)
class DriverSessionController:
    driver_session_service: DriverSessionService = Injected(DriverSessionService)

    @driver_session_router.post("/drivers/{driver_id}/driver_sessions/login")
    def log_in(self, driver_id: int, dto: DriverSessionDTO):
        self.driver_session_service.log_in(driver_id, dto.plates_number, dto.car_class, dto.car_brand)
        return {}

    @driver_session_router.delete("/drivers/{driver_id}/driver_sessions/{session_id}")
    def log_out(self, driver_id: int, session_id: int):
        self.driver_session_service.log_out(session_id)
        return {}

    @driver_session_router.delete("/drivers/{driver_id}/driver_sessions/")
    def log_out_current(self, driver_id: int):
        self.driver_session_service.log_out_current_session(driver_id)
        return {}

    @driver_session_router.get("/drivers/{driver_id}/driver_sessions/login")
    def list(self, driver_id: int) -> List[DriverSessionDTO]:
        return list(
            map(
                lambda s: DriverSessionDTO(**s.dict()),
                self.driver_session_service.find_by_driver(driver_id)
            )
        )
