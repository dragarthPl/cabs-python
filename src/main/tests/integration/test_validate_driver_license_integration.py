from unittest import TestCase

from fastapi.params import Depends
from core.database import create_db_and_tables, drop_db_and_tables

from dto.driver_dto import DriverDTO
from entity import Driver
from service.driver_service import DriverService
from tests.fixtures import resolve_dependency


class TestValidateDriverLicenseIntegration(TestCase):
    driver_service: DriverService = resolve_dependency(Depends(DriverService))

    def setUp(self):
        create_db_and_tables()

    def test_cannot_create_active_driver_with_invalid_license(self):
        # expect
        with self.assertRaises(ValueError):
            self.create_active_driver_with_license("invalidLicense")

    def test_can_create_active_driver_with_valid_license(self):
        # when

        driver: Driver = self.create_active_driver_with_license("FARME100165AB5EW")

        # then
        loaded: DriverDTO = self.load(driver)
        self.assertEqual("FARME100165AB5EW", loaded.driver_license)
        self.assertEqual(Driver.Status.ACTIVE, loaded.status)

    def test_can_create_inactive_driver_with_invalid_license(self):
        # when

        driver: Driver = self.create_inactive_driver_with_license("invalidlicense")

        # then
        loaded: DriverDTO = self.load(driver)
        self.assertEqual("invalidlicense", loaded.driver_license)
        self.assertEqual(Driver.Status.INACTIVE, loaded.status)

    def test_can_change_license_for_valid_one(self):
        # given
        driver: Driver = self.create_active_driver_with_license("FARME100165AB5EW")

        # when
        self.change_license_to("99999740614992TL", driver)

        # then
        loaded: DriverDTO = self.load(driver)
        self.assertEqual("99999740614992TL", loaded.driver_license)

    def test_cannot_change_license_for_invalid_one(self):
        # given
        driver: Driver = self.create_active_driver_with_license("FARME100165AB5EW")

        # expect
        with self.assertRaises(ValueError):
            self.change_license_to("invalid", driver)

    def test_can_activate_driver_with_valid_license(self):
        # given
        driver: Driver = self.create_active_driver_with_license("FARME100165AB5EW")

        # when
        self.activate(driver)

        # then
        self.assertEqual(Driver.Status.ACTIVE, driver.status)

    def test_cannot_activate_driver_with_invalid_license(self):
        # given
        driver: Driver = self.create_inactive_driver_with_license("invalid")

        # expect
        with self.assertRaises(ValueError):
            self.activate(driver)

    def create_active_driver_with_license(self, driver_license: str) -> Driver:
        return self.driver_service.create_driver(
            driver_license,
            "Kowalski",
            "Jan",
            Driver.Type.REGULAR,
            Driver.Status.ACTIVE,
            "photo"
        )

    def create_inactive_driver_with_license(self, driver_license: str) -> Driver:
        return self.driver_service.create_driver(
            driver_license,
            "Kowalski",
            "Jan",
            Driver.Type.REGULAR,
            Driver.Status.INACTIVE,
            "photo"
        )

    def load(self, driver: Driver) -> DriverDTO:
        loaded = self.driver_service.load_driver(driver.id)
        return loaded

    def change_license_to(self, new_license: str, driver: Driver):
        self.driver_service.change_license_number(new_license, driver.id)

    def activate(self, driver: Driver):
        self.driver_service.change_driver_status(driver.id, Driver.Status.ACTIVE)

    def tearDown(self) -> None:
        drop_db_and_tables()