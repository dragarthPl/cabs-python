from unittest import TestCase

from fastapi.params import Depends
from mockito import verify, mock, when, ANY, verifyZeroInteractions

from core.database import create_db_and_tables, drop_db_and_tables
from driverreport.driver_report_creator import DriverReportCreator
from driverreport.old_driver_report_creator import OldDriverReportCreator
from driverreport.sql_based_driver_report_creator import SqlBasedDriverReportCreator
from dto.driver_report import DriverReport
from tests.common.fixtures import DependencyResolver

dependency_resolver = DependencyResolver()


class TestDriverReportCreator(TestCase):
    LAST_DAYS: int = 3
    DRIVER_ID: int = 1
    SQL_REPORT = DriverReport()
    OLD_REPORT = DriverReport()

    report_creator: DriverReportCreator = dependency_resolver.resolve_dependency(Depends(DriverReportCreator))
    old_driver_report_creator: OldDriverReportCreator = dependency_resolver.resolve_dependency(
        Depends(OldDriverReportCreator))
    sql_based_driver_report_creator: SqlBasedDriverReportCreator = dependency_resolver.resolve_dependency(
        Depends(DriverReportCreator))

    def setUp(self):
        self.report_creator.sql_based_driver_report_creator = mock()
        self.report_creator.old_driver_report_creator = mock()
        self.report_creator.driver_report_reconciliation = mock()
        create_db_and_tables()

    def test_calls_new_report(self):
        # given
        self.report_creator.feature_flags.feature_flags_settings.DRIVER_REPORT_CREATION_RECONCILIATION = False
        self.report_creator.feature_flags.feature_flags_settings.DRIVER_REPORT_SQL = True

        # when
        self.report_creator.create(self.DRIVER_ID, self.LAST_DAYS)

        # then
        verify(self.report_creator.sql_based_driver_report_creator).create_report(self.DRIVER_ID, self.LAST_DAYS)
        verifyZeroInteractions(self.report_creator.old_driver_report_creator)

    def test_calls_old_report(self):
        # given
        self.report_creator.feature_flags.feature_flags_settings.DRIVER_REPORT_CREATION_RECONCILIATION = False
        self.report_creator.feature_flags.feature_flags_settings.DRIVER_REPORT_SQL = False

        # when
        self.report_creator.create(self.DRIVER_ID, self.LAST_DAYS)

        # then
        verify(self.report_creator.old_driver_report_creator).create_report(self.DRIVER_ID, self.LAST_DAYS)
        verifyZeroInteractions(self.report_creator.sql_based_driver_report_creator)

    def test_calls_reconciliation_and_uses_old_report(self):
        # given
        self.both_ways_return_report()
        self.report_creator.feature_flags.feature_flags_settings.DRIVER_REPORT_CREATION_RECONCILIATION = True
        self.report_creator.feature_flags.feature_flags_settings.DRIVER_REPORT_SQL = False

        # when
        self.report_creator.create(self.DRIVER_ID, self.LAST_DAYS)

        # then
        verify(self.report_creator.old_driver_report_creator).create_report(self.DRIVER_ID, self.LAST_DAYS)
        verify(self.report_creator.sql_based_driver_report_creator).create_report(self.DRIVER_ID, self.LAST_DAYS)
        verify(self.report_creator.driver_report_reconciliation).compare(self.OLD_REPORT, self.SQL_REPORT)

    def test_calls_reconciliation_and_uses_new_report(self):
        # given
        self.both_ways_return_report()
        self.report_creator.feature_flags.feature_flags_settings.DRIVER_REPORT_CREATION_RECONCILIATION = True
        self.report_creator.feature_flags.feature_flags_settings.DRIVER_REPORT_SQL = True

        # when
        self.report_creator.create(self.DRIVER_ID, self.LAST_DAYS)

        # then
        verify(self.report_creator.sql_based_driver_report_creator).create_report(self.DRIVER_ID, self.LAST_DAYS)
        verify(self.report_creator.old_driver_report_creator).create_report(self.DRIVER_ID, self.LAST_DAYS)
        verify(self.report_creator.driver_report_reconciliation).compare(self.OLD_REPORT, self.SQL_REPORT)

    def both_ways_return_report(self):
        self.old_way_returns_report()
        self.new_sql_way_returns_report()

    def new_sql_way_returns_report(self):
        when(
            self.report_creator.sql_based_driver_report_creator
        ).create_report(self.DRIVER_ID, self.LAST_DAYS).thenReturn(self.SQL_REPORT)

    def old_way_returns_report(self):
        when(
            self.report_creator.old_driver_report_creator
        ).create_report(self.DRIVER_ID, self.LAST_DAYS).thenReturn(self.OLD_REPORT)

    def tearDown(self) -> None:
        drop_db_and_tables()
