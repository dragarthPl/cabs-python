from unittest import TestCase

from driverfleet.driver_license import DriverLicense


class TestDriverLicense(TestCase):

    def test_cannot_create_invalid_license(self):
        with self.assertRaises(ValueError):
            DriverLicense.with_license("invalid")
        with self.assertRaises(ValueError):
            DriverLicense.with_license("")

    def test_can_create_valid_license(self):
        # when
        license: DriverLicense = DriverLicense.with_license("FARME100165AB5EW")

        # then
        self.assertEqual("FARME100165AB5EW", license.as_string())

    def test_can_create_invalid_license_explicitly(self):
        # when
        license: DriverLicense = DriverLicense.without_validation("invalid")

        # then
        self.assertEqual("invalid", license.as_string())
