from abc import ABCMeta
from typing import Optional

from config.feature_flags import FeatureFlags, get_feature_flags
from driverreport.old_driver_report_creator import OldDriverReportCreator
from driverreport.sql_based_driver_report_creator import SqlBasedDriverReportCreator
from dto.driver_report import DriverReport
from fastapi import Depends


class DriverReportReconciliation(metaclass=ABCMeta):
    def compare(self, old_one: DriverReport, new_one: DriverReport) -> None:
        raise NotImplementedError()


class TestDummyReconciliation(DriverReportReconciliation):
    def compare(self, old_one: DriverReport, new_one: DriverReport) -> None:
        pass


class DriverReportCreator:
    sql_based_driver_report_creator: SqlBasedDriverReportCreator
    old_driver_report_creator: OldDriverReportCreator
    feature_flags: FeatureFlags
    driver_report_reconciliation: DriverReportReconciliation

    def __init__(
        self,
        sql_based_driver_report_creator: SqlBasedDriverReportCreator = Depends(SqlBasedDriverReportCreator),
        old_driver_report_creator: OldDriverReportCreator = Depends(OldDriverReportCreator),
        feature_flags: FeatureFlags = Depends(get_feature_flags),
        driver_report_reconciliation: DriverReportReconciliation = Depends(TestDummyReconciliation),
    ):
        self.sql_based_driver_report_creator = sql_based_driver_report_creator
        self.old_driver_report_creator = old_driver_report_creator
        self.feature_flags = feature_flags
        self.driver_report_reconciliation = driver_report_reconciliation

    def create(self, driver_id: int, days: int) -> DriverReport:
        new_report: Optional[DriverReport] = None
        old_report: Optional[DriverReport] = None
        if self.__should_compare():
            new_report = self.sql_based_driver_report_creator.create_report(driver_id, days)
            old_report = self.old_driver_report_creator.create_report(driver_id, days)
            self.driver_report_reconciliation.compare(old_report, new_report)
        if self.__should_use_new_report():
            if not new_report:
                new_report = self.sql_based_driver_report_creator.create_report(driver_id, days)
            return new_report
        if not old_report:
            old_report = self.old_driver_report_creator.create_report(driver_id, days)
        return old_report

    def __should_compare(self):
        return self.feature_flags.DRIVER_REPORT_CREATION_RECONCILIATION.is_active()

    def __should_use_new_report(self):
        return self.feature_flags.DRIVER_REPORT_SQL.is_active()

