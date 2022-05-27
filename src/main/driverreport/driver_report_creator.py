from config.feature_flags import FeatureFlags, get_feature_flags
from driverreport.old_driver_report_creator import OldDriverReportCreator
from driverreport.sql_based_driver_report_creator import SqlBasedDriverReportCreator
from dto.driver_report import DriverReport
from fastapi import Depends


class DriverReportCreator:
    sql_based_driver_report_creator: SqlBasedDriverReportCreator
    old_driver_report_creator: OldDriverReportCreator
    feature_flags: FeatureFlags

    def __init__(
        self,
        sql_based_driver_report_creator: SqlBasedDriverReportCreator = Depends(SqlBasedDriverReportCreator),
        old_driver_report_creator: OldDriverReportCreator = Depends(OldDriverReportCreator),
        feature_flags: FeatureFlags = Depends(get_feature_flags),
    ):
        self.sql_based_driver_report_creator = sql_based_driver_report_creator
        self.old_driver_report_creator = old_driver_report_creator
        self.feature_flags = feature_flags

    def create(self, driver_id: int, days: int) -> DriverReport:
        if self.__should_use_new_report():
            return self.sql_based_driver_report_creator.create_report(driver_id, days)
        return self.old_driver_report_creator.create_report(driver_id, days)

    def __should_use_new_report(self):
        return self.feature_flags.DRIVER_REPORT_SQL.is_active()
