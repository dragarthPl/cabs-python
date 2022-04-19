import re


class DriverLicense:
    DRIVER_LICENSE_REGEX = "^[A-Z9]{5}\\d{6}[A-Z9]{2}\\d[A-Z]{2}$"

    driver_license: str

    def __init__(self, driver_license: str):
        self.driver_license = driver_license

    @classmethod
    def with_license(cls, driver_license: str) -> 'DriverLicense':
        license_regexp = re.compile(cls.DRIVER_LICENSE_REGEX)
        if not driver_license or not license_regexp.match(driver_license):
            raise ValueError("Illegal license no = " + driver_license)
        return cls(driver_license)

    @staticmethod
    def without_validation(driver_license: str) -> 'DriverLicense':
        return DriverLicense(driver_license)

    def __str__(self) -> str:
        return f"DriverLicense{{driverLicense='{self.driver_license}'}}"

    def as_string(self) -> str:
        return self.driver_license
