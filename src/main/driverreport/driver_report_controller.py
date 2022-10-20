from typing import Optional

from fastapi_injector import Injected

from dto.driver_report import DriverReport
from fastapi_utils.cbv import cbv
from fastapi_utils.inferring_router import InferringRouter
from driverreport.sql_based_driver_report_creator import SqlBasedDriverReportCreator

driver_report_router = InferringRouter(tags=["DriverReportController"])


@cbv(driver_report_router)
class DriverReportController:
    driver_report_creator: SqlBasedDriverReportCreator = Injected(SqlBasedDriverReportCreator)

    @driver_report_router.get("/driverreport/{driver_id}")
    def load_report_for_driver(self, driver_id: int, last_days: Optional[int] = 0) -> DriverReport:
        return self.driver_report_creator.create_report(driver_id, last_days)
