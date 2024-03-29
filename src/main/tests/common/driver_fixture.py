from datetime import datetime
from random import random

from injector import inject
from mockito import when, arg_that

from carfleet.car_class import CarClass
from driverfleet.driver import Driver
from driverfleet.driver_attribute import DriverAttribute
from driverfleet.driver_attribute_name import DriverAttributeName
from driverfleet.driver_fee import DriverFee
from geolocation.address.address import Address
from money import Money
from driverfleet.driver_attribute_repository import DriverAttributeRepositoryImp
from driverfleet.driver_fee_repository import DriverFeeRepositoryImp
from driverfleet.driver_fee_service import DriverFeeService
from driverfleet.driver_service import DriverService
from tests.common.address_matcher import AddressMatcher
from tracking.driver_session_service import DriverSessionService
from tracking.driver_tracking_service import DriverTrackingService
from geolocation.geocoding_service import GeocodingService


class DriverFixture:
    fee_repository: DriverFeeRepositoryImp
    driver_service: DriverService
    driver_attribute_repository: DriverAttributeRepositoryImp
    driver_session_service: DriverSessionService
    driver_tracking_service: DriverTrackingService
    driver_fee_service: DriverFeeService

    @inject
    def __init__(
        self,
        fee_repository: DriverFeeRepositoryImp,
        driver_service: DriverService,
        driver_attribute_repository: DriverAttributeRepositoryImp,
        driver_session_service: DriverSessionService,
        driver_tracking_service: DriverTrackingService,
        driver_fee_service: DriverFeeService,
    ):
        self.fee_repository = fee_repository
        self.driver_service = driver_service
        self.driver_attribute_repository = driver_attribute_repository
        self.driver_session_service = driver_session_service
        self.driver_tracking_service = driver_tracking_service
        self.driver_fee_service = driver_fee_service

    def driver_has_min_fee(self, driver: Driver, fee_type: DriverFee.FeeType, amount: int, min: int):
        driver_fee = self.fee_repository.find_by_driver_id(driver.id)
        if not driver_fee:
            driver_fee = DriverFee()
        driver_fee.driver = driver
        driver_fee.amount = amount
        driver_fee.fee_type = fee_type
        driver_fee.set_min(Money(min))
        return self.fee_repository.save(driver_fee)

    def driver_has_fee(self, driver: Driver, fee_type: DriverFee.FeeType, amount: int) -> DriverFee:
        return self.driver_has_min_fee(driver, fee_type, amount, 0)

    def an_active_regular_driver(self) -> Driver:
        return self.a_driver(
            Driver.Status.ACTIVE,
            "Janusz",
            "Kowalsi",
            "FARME100165AB5EW",
        )

    def a_driver(self, status: Driver.Status, name: str, last_name: str, driver_license: str) -> Driver:
        return self.driver_service.create_driver(
            driver_license,
            last_name,
            name,
            Driver.Type.REGULAR,
            status,
            "",
        )

    def a_nearby_driver_only_stubbed(
            self,
            stubbed_geocoding_service: GeocodingService,
            pickup: Address,
            latitude: float,
            longitude: float
    ) -> Driver:
        when(stubbed_geocoding_service).geocode_address(
            AddressMatcher(pickup)
        ).thenReturn([latitude, longitude])
        return self.a_nearby_driver("WU DAMIAN", latitude, longitude, CarClass.VAN, datetime.now(), "brand")

    def a_random_nearby_driver(self, stubbed_geocoding_service: GeocodingService, pickup: Address) -> Driver:
        latitude: float = random()
        longitude: float = random()
        return self.a_nearby_driver_only_stubbed(
            stubbed_geocoding_service, pickup, latitude, longitude)

    def a_nearby_driver_default(
        self,
        stubbed_geocoding_service: GeocodingService,
        pickup: Address,
        latitude: float,
        longitude: float,
    ) -> Driver:
        when(
            stubbed_geocoding_service
        ).geocode_address(
            arg_that(AddressMatcher(pickup).matches)
        ).thenReturn([latitude, longitude])
        return self.a_nearby_driver("WU DAMIAN", latitude, longitude, CarClass.VAN, datetime.now(), "brand")

    def a_nearby_driver(
        self,
        plate_number: str,
        latitude: float,
        longitude: float,
        car_class: CarClass,
        when: datetime,
        car_brand: str
    ) -> Driver:
        driver: Driver = self.an_active_regular_driver()
        self.driver_has_fee(driver, DriverFee.FeeType.FLAT, 10)
        self.driver_logs_in(plate_number, car_class, driver, car_brand)
        return self.driver_is_at_geo_localization(
            plate_number, latitude, longitude, car_class, driver, when, car_brand)

    def driver_is_at_geo_localization(
        self,
        plate_number: str,
        latitude: float,
        longitude: float,
        car_class: CarClass,
        driver: Driver,
        since: datetime,
        car_brand: str
    ) -> Driver:
        self.driver_tracking_service.register_position(driver.id, latitude, longitude, since)
        return driver

    def driver_logs_in(self, plate_number: str, car_class: CarClass, driver: Driver, car_brand: str) -> None:
        self.driver_session_service.log_in(driver.id, plate_number, car_class, car_brand)

    def driver_has_attribute(self, driver: Driver, name: DriverAttributeName, value: str):
        self.driver_attribute_repository.save(DriverAttribute(driver=driver, name=name, value=value))
