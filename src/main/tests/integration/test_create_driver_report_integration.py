from datetime import datetime
from typing import List
from unittest import IsolatedAsyncioTestCase

import pytz
from fastapi_events import middleware_identifier
from freezegun import freeze_time
from dateutil.relativedelta import relativedelta
from httpx import AsyncClient
from mockito import when

from carfleet.car_class import CarClass
from core.database import create_db_and_tables, drop_db_and_tables
from carfleet.car_type_dto import CarTypeDTO
from driverfleet.driver import Driver
from driverfleet.driver_attribute_dto import DriverAttributeDTO
from driverfleet.driver_attribute_name import DriverAttributeName
from driverfleet.driver_fee import DriverFee
from driverfleet.driverreport.driver_report import DriverReport
from ride.transit_dto import TransitDTO
from crm.client import Client
from geolocation.address.address import Address
from geolocation.address.address_repository import AddressRepositoryImp
from crm.claims.claim_service import ClaimService
from tests.common.ride_fixture import RideFixture
from geolocation.geocoding_service import GeocodingService
from tests.common.fixtures import DependencyResolver, Fixtures
from driverfleet.driverreport.driver_report_controller import DriverReportController
from driverfleet.driverreport.sql_based_driver_report_creator import SqlBasedDriverReportCreator

from cabs_application import CabsApplication

dependency_resolver = DependencyResolver()


class TestCreateDriverReportIntegration(IsolatedAsyncioTestCase):
    DAY_BEFORE_YESTERDAY = datetime(1989, 12, 12, 12, 12).astimezone(pytz.utc)
    YESTERDAY = DAY_BEFORE_YESTERDAY + relativedelta(days=1)
    TODAY = YESTERDAY + relativedelta(days=1)

    fixtures: Fixtures = dependency_resolver.resolve_dependency(Fixtures)
    ride_fixture: RideFixture = dependency_resolver.resolve_dependency(RideFixture)
    driver_report_controller: DriverReportController = DriverReportController(
        driver_report_creator=dependency_resolver.resolve_dependency(SqlBasedDriverReportCreator)
    )
    address_repository: AddressRepositoryImp = dependency_resolver.resolve_dependency(AddressRepositoryImp)
    geocoding_service: GeocodingService = dependency_resolver.resolve_dependency(GeocodingService)
    claim_service: ClaimService = dependency_resolver.resolve_dependency(ClaimService)

    async def asyncSetUp(self):
        create_db_and_tables()
        app = CabsApplication().create_app()
        middleware_identifier.set(app.middleware_stack.app._id)

        self.client = AsyncClient(app=app)
        self.fixtures.an_active_car_category(CarClass.VAN)
        self.fixtures.an_active_car_category(CarClass.PREMIUM)

    async def test_should_create_drivers_report(self):
        # given
        client = self.fixtures.a_client()
        # and
        driver = self.a_driver(Driver.Status.ACTIVE, "JAN", "NOWAK", "FARME100165AB5EW")
        # and
        self.fixtures.driver_has_attribute(
            driver, DriverAttributeName.COMPANY_NAME, "UBER")
        self.fixtures.driver_has_attribute(
            driver, DriverAttributeName.PENALTY_POINTS, "21")
        self.fixtures.driver_has_attribute(
            driver, DriverAttributeName.MEDICAL_EXAMINATION_REMARKS, "private info")
        # and
        self.ride_fixture.driver_has_done_session_and_picks_someone_up_in_car(
            driver,
            client,
            CarClass.VAN,
            "WU1213",
            "SCODA FABIA",
            self.TODAY,
            self.geocoding_service
        )
        self.ride_fixture.driver_has_done_session_and_picks_someone_up_in_car(
            driver,
            client,
            CarClass.VAN,
            "WU1213",
            "SCODA OCTAVIA",
            self.YESTERDAY,
            self.geocoding_service,
        )
        in_bmw: TransitDTO = self.ride_fixture.driver_has_done_session_and_picks_someone_up_in_car(
            driver,
            client,
            CarClass.VAN,
            "WU1213",
            "BMW M2",
            self.DAY_BEFORE_YESTERDAY,
            self.geocoding_service,
        )
        # and
        self.fixtures.create_claim_reason(client, in_bmw, "za szybko")

        # when
        driver_report_within_2_days = self.load_report_including_past_days(driver, 2)
        driver_report_within_1_day = self.load_report_including_past_days(driver, 1)
        driver_report_for_just_today = self.load_report_including_past_days(driver, 0)

        # then
        self.assertEqual(3, len(driver_report_within_2_days.sessions.keys()))
        self.assertEqual(2, len(driver_report_within_1_day.sessions.keys()))
        self.assertEqual(1, len(driver_report_for_just_today.sessions.keys()))

        self.assertEqual("FARME100165AB5EW", driver_report_within_2_days.driver_dto.driver_license)
        self.assertEqual("JAN", driver_report_within_2_days.driver_dto.first_name)
        self.assertEqual("NOWAK", driver_report_within_2_days.driver_dto.last_name)
        self.assertEqual(2, len(driver_report_within_2_days.attributes))
        self.assertIn(
            DriverAttributeDTO(
                name=DriverAttributeName.COMPANY_NAME,
                value="UBER"
            ),
            driver_report_within_2_days.attributes
        )
        self.assertIn(
            DriverAttributeDTO(
                name=DriverAttributeName.PENALTY_POINTS,
                value="21"
            ),
            driver_report_within_2_days.attributes
        )
        self.assertEqual(1, len(self.transits_in_session_in("SCODA FABIA", driver_report_within_2_days)))
        self.assertIsNone(self.transits_in_session_in("SCODA FABIA", driver_report_within_2_days)[0].claim_dto)

        self.assertEqual(1, len(self.transits_in_session_in("SCODA OCTAVIA", driver_report_within_2_days)))
        self.assertIsNone(self.transits_in_session_in("SCODA OCTAVIA", driver_report_within_2_days)[0].claim_dto)

        self.assertEqual(1, len(self.transits_in_session_in("BMW M2", driver_report_within_2_days)))
        self.assertIsNotNone(self.transits_in_session_in("BMW M2", driver_report_within_2_days)[0].claim_dto)
        self.assertEqual(
            "za szybko",
            self.transits_in_session_in("BMW M2", driver_report_within_2_days)[0].claim_dto.reason
        )

    def load_report_including_past_days(self, driver: Driver, days: int) -> DriverReport:
        with freeze_time(self.TODAY):
            return self.driver_report_controller.load_report_for_driver(driver.id, days)

    def transits_in_session_in(self, car_brand: str, driver_report: DriverReport) -> List[TransitDTO]:
        return list(map(
            lambda value: value[1][0],
            dict(filter(
                lambda value: value[0].car_brand == car_brand,
                driver_report.sessions.items()
            )).items()
        ))

    def a_driver(self, status: Driver.Status, name: str, last_name: str, driver_license: str) -> Driver:
        driver = self.fixtures.a_driver(status, name, last_name, driver_license)
        self.fixtures.driver_has_fee(driver, DriverFee.FeeType.FLAT, 10)
        return driver

    async def asyncTearDown(self) -> None:
        drop_db_and_tables()
