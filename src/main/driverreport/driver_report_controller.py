from typing import Optional

from dto.driver_report import DriverReport
from fastapi import Depends
from fastapi_utils.cbv import cbv
from fastapi_utils.inferring_router import InferringRouter
from repository.claim_repository import ClaimRepositoryImp
from repository.driver_repository import DriverRepositoryImp
from repository.driver_session_repository import DriverSessionRepositoryImp
from service.driver_service import DriverService
from driverreport.sql_based_driver_report_creator import SqlBasedDriverReportCreator

driver_report_router = InferringRouter(tags=["DriverReportController"])


@cbv(driver_report_router)
class DriverReportController:
    driver_service: DriverService = Depends(DriverService)
    driver_repository: DriverRepositoryImp = Depends(DriverRepositoryImp)
    claim_repository: ClaimRepositoryImp = Depends(ClaimRepositoryImp)
    driver_session_repository: DriverSessionRepositoryImp = Depends(DriverSessionRepositoryImp)
    sql_based_driver_report_creator: SqlBasedDriverReportCreator = Depends(SqlBasedDriverReportCreator)

    @driver_report_router.get("/driverreport/{driver_id}")
    def load_report_for_driver(self, driver_id: int, last_days: Optional[int] = 0) -> DriverReport:
        return self.sql_based_driver_report_creator.create_report(driver_id, last_days)
