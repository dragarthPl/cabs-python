from datetime import datetime
from typing import List
from unittest import TestCase

import pytz
from freezegun import freeze_time
from dateutil.relativedelta import relativedelta
from fastapi.params import Depends
from mockito import when

from core.database import create_db_and_tables, drop_db_and_tables
from dto.car_type_dto import CarTypeDTO
from dto.driver_attribute_dto import DriverAttributeDTO
from dto.driver_report import DriverReport
from dto.transit_dto import TransitDTO
from entity import CarType, Driver, DriverFee, DriverAttribute, Client, Transit, Address
from repository.address_repository import AddressRepositoryImp
from repository.claim_repository import ClaimRepositoryImp
from repository.driver_repository import DriverRepositoryImp
from repository.driver_session_repository import DriverSessionRepositoryImp
from service.car_type_service import CarTypeService
from service.claim_service import ClaimService
from service.driver_service import DriverService
from service.driver_session_service import DriverSessionService
from service.driver_tracking_service import DriverTrackingService
from service.geocoding_service import GeocodingService
from service.transit_service import TransitService
from tests.common.fixtures import DependencyResolver, Fixtures
from ui.driver_report_controller import DriverReportController

dependency_resolver = DependencyResolver()

class TestCreateDriverReportIntegration(TestCase):
    DAY_BEFORE_YESTERDAY = datetime(1989, 12, 12, 12, 12).astimezone(pytz.utc)
    YESTERDAY = DAY_BEFORE_YESTERDAY + relativedelta(days=1)
    TODAY = YESTERDAY + relativedelta(days=1)

    transit_service: TransitService = dependency_resolver.resolve_dependency(Depends(TransitService))
    driver_tracking_service: DriverTrackingService = dependency_resolver.resolve_dependency(
        Depends(DriverTrackingService))
    driver_session_service: DriverSessionService = dependency_resolver.resolve_dependency(Depends(DriverSessionService))
    car_type_service: CarTypeService = dependency_resolver.resolve_dependency(Depends(CarTypeService))
    fixtures: Fixtures = dependency_resolver.resolve_dependency(Depends(Fixtures))
    driver_report_controller: DriverReportController = DriverReportController(
        driver_service=dependency_resolver.resolve_dependency(Depends(DriverService)),
        driver_repository=dependency_resolver.resolve_dependency(Depends(DriverRepositoryImp)),
        claim_repository=dependency_resolver.resolve_dependency(Depends(ClaimRepositoryImp)),
        driver_session_repository=dependency_resolver.resolve_dependency(Depends(DriverSessionRepositoryImp)),
    )
    address_repository: AddressRepositoryImp = dependency_resolver.resolve_dependency(Depends(AddressRepositoryImp))
    geocoding_service: GeocodingService = dependency_resolver.resolve_dependency(Depends(GeocodingService))
    claim_service: ClaimService = dependency_resolver.resolve_dependency(Depends(ClaimService))

    def setUp(self):
        create_db_and_tables()
        self.an_active_car_category(CarType.CarClass.VAN)
        self.an_active_car_category(CarType.CarClass.PREMIUM)

    def test_should_create_drivers_report(self):
        # given
        client = self.fixtures.a_client()
        # and
        driver = self.a_driver(Driver.Status.ACTIVE, "JAN", "NOWAK", "FARME100165AB5EW")
        # and
        self.fixtures.driver_has_attribute(
            driver, DriverAttribute.DriverAttributeName.COMPANY_NAME, "UBER")
        self.fixtures.driver_has_attribute(
            driver, DriverAttribute.DriverAttributeName.PENALTY_POINTS, "21")
        self.fixtures.driver_has_attribute(
            driver, DriverAttribute.DriverAttributeName.MEDICAL_EXAMINATION_REMARKS, "private info")
        # and
        self.driver_has_done_session_and_picks_someone_up_in_car(
            driver, client, CarType.CarClass.VAN, "WU1213", "SCODA FABIA", self.TODAY)
        self.driver_has_done_session_and_picks_someone_up_in_car(
            driver, client, CarType.CarClass.VAN, "WU1213", "SCODA OCTAVIA", self.YESTERDAY)
        in_bmw = self.driver_has_done_session_and_picks_someone_up_in_car(
            driver, client, CarType.CarClass.VAN, "WU1213", "BMW M2", self.DAY_BEFORE_YESTERDAY)
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
                name=DriverAttribute.DriverAttributeName.COMPANY_NAME,
                value="UBER"
            ),
            driver_report_within_2_days.attributes
        )
        self.assertIn(
            DriverAttributeDTO(
                name=DriverAttribute.DriverAttributeName.PENALTY_POINTS,
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

    def driver_has_done_session_and_picks_someone_up_in_car(
        self,
        driver: Driver,
        client: Client,
        car_class: CarType.CarClass,
        plate_number: str,
        car_brand: str,
        when: datetime,
    ) -> Transit:
        with freeze_time(when):
            driver_id = driver.id
            self.driver_session_service.log_in(driver_id, plate_number, car_class, car_brand)
            self.driver_tracking_service.register_position(driver_id, 10, 20)
            address_to = self.address("PL", "MAZ", "WAW", "STREET", 100, 10.01, 20.01)
            transit = self.transit_service.create_transit_transaction(
                client.id,
                self.address("PL", "MAZ", "WAW", "STREET", 1, 10, 20),
                address_to,
                car_class
            )
            self.transit_service.publish_transit(transit.id)
            self.transit_service.accept_transit(driver_id, transit.id)
            self.transit_service.start_transit(driver_id, transit.id)
            self.transit_service._complete_transit(
                driver_id,
                transit.id,
                address_to
            )
            self.driver_session_service.log_out_current_session(driver_id)
            return transit

    def a_driver(self, status: Driver.Status, name: str, last_name: str, driver_license: str) -> Driver:
        driver = self.fixtures.a_driver(status, name, last_name, driver_license)
        self.fixtures.driver_has_fee(driver, DriverFee.FeeType.FLAT, 10)
        return driver

    def address(
        self,
        country: str,
        district: str,
        city: str,
        street: str,
        building_number: int,
        latitude: float,
        longitude: float,
    ) -> Address:
        address = Address()
        address.country = country
        address.district = district
        address.city = city
        address.street = street
        address.building_number = building_number
        address = self.address_repository.save(address)
        when(self.geocoding_service).geocode_address(address).thenReturn([latitude, longitude])
        return address

    def an_active_car_category(self, car_class: CarType.CarClass) -> CarType:
        car_type_dto = CarTypeDTO()
        car_type_dto.car_class = car_class
        car_type_dto.description = "opis"
        car_type = self.car_type_service.create(car_type_dto)
        for _ in range(car_type.min_no_of_cars_to_activate_class + 1):
            self.car_type_service.register_car(car_type.car_class)
        self.car_type_service.activate(car_type.id)
        return car_type

    def tearDown(self) -> None:
        drop_db_and_tables()
