from unittest import TestCase

from fastapi.params import Depends
from mockito import verify, mock, when, ANY

from core.database import create_db_and_tables, drop_db_and_tables
from driverreport.driver_report_creator import DriverReportCreator
from driverreport.old_driver_report_creator import OldDriverReportCreator
from driverreport.sql_based_driver_report_creator import SqlBasedDriverReportCreator
from tests.common.fixtures import DependencyResolver

dependency_resolver = DependencyResolver()


class TestDriverReportCreator(TestCase):
    LAST_DAYS: int = 3
    DRIVER_ID: int = 1

    driver_report_creator: DriverReportCreator = dependency_resolver.resolve_dependency(Depends(DriverReportCreator))
    old_driver_report_creator: OldDriverReportCreator = dependency_resolver.resolve_dependency(
        Depends(OldDriverReportCreator))
    sql_based_driver_report_creator: SqlBasedDriverReportCreator = dependency_resolver.resolve_dependency(
        Depends(DriverReportCreator))

    def setUp(self):
        self.driver_report_creator.sql_based_driver_report_creator = mock()
        self.driver_report_creator.old_driver_report_creator = mock()
        create_db_and_tables()

    def test_calls_new_report(self):
        # when
        self.driver_report_creator.feature_flags.feature_flags_settings.DRIVER_REPORT_SQL = True
        self.driver_report_creator.create(self.DRIVER_ID, self.LAST_DAYS)

        # then
        verify(self.driver_report_creator.sql_based_driver_report_creator).create_report(self.DRIVER_ID, self.LAST_DAYS)

    def test_calls_old_report(self):
        # when
        self.driver_report_creator.feature_flags.feature_flags_settings.DRIVER_REPORT_SQL = False
        self.driver_report_creator.create(self.DRIVER_ID, self.LAST_DAYS)

        # then
        verify(self.driver_report_creator.old_driver_report_creator).create_report(self.DRIVER_ID, self.LAST_DAYS)

    def tearDown(self) -> None:
        drop_db_and_tables()
