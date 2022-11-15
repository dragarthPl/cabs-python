from typing import Optional

from fastapi_injector import Injected

from driverfleet.driver import Driver
from driverfleet.driver_dto import DriverDTO
from fastapi_utils.cbv import cbv
from fastapi_utils.inferring_router import InferringRouter
from driverfleet.driver_repository import DriverRepositoryImp
from driverfleet.driver_service import DriverService

driver_router = InferringRouter(tags=["DriverController"])

@cbv(driver_router)
class DriverController:
    driver_service: DriverService = Injected(DriverService)
    driver_repository: DriverRepositoryImp = Injected(DriverRepositoryImp)

    @driver_router.post("/drivers")
    def create_driver(self, license: str, first_name: str, last_name: str, photo: Optional[str] = None) -> DriverDTO:
        driver = self.driver_service.create_driver(
            license, last_name, first_name, Driver.Type.CANDIDATE, Driver.Status.INACTIVE, photo)

        return self.driver_service.load_driver(driver.id)

    @driver_router.get("/drivers/{driver_id}")
    def get_driver(self, driver_id: int) -> DriverDTO:
        return self.driver_service.load_driver(driver_id)

    @driver_router.post("/drivers/{driver_id}")
    def update_driver(self, driver_id: int) -> DriverDTO:
        return self.driver_service.load_driver(driver_id)

    @driver_router.post("/drivers/{driver_id}/deactivate")
    def deactivate_driver(self, driver_id: int) -> DriverDTO:
        self.driver_service.change_driver_status(driver_id, Driver.Status.INACTIVE)

        return self.driver_service.load_driver(driver_id)

    @driver_router.post("/drivers/{driver_id}/activate")
    def activate_driver(self, driver_id: int) -> DriverDTO:
        self.driver_service.change_driver_status(driver_id, Driver.Status.ACTIVE)

        return self.driver_service.load_driver(driver_id)
