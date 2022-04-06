import base64
import calendar
import re
from datetime import datetime
from functools import reduce
from typing import Dict

from dto.driver_dto import DriverDTO
from entity import Driver, DriverAttribute
from fastapi import Depends
from repository.driver_attribute_repository import DriverAttributeRepositoryImp
from repository.driver_repository import DriverRepositoryImp
from repository.transit_repository import TransitRepositoryImp
from service.driver_fee_service import DriverFeeService


def is_base_64(s):
    try:
        return base64.b64encode(base64.b64decode(s)) == s
    except Exception:
        return False


class DriverService:
    DRIVER_LICENSE_REGEX = "^[A-Z9]{5}\\d{6}[A-Z9]{2}\\d[A-Z]{2}$"
    driver_repository: DriverRepositoryImp
    driver_attribute_repository: DriverAttributeRepositoryImp
    transit_repository: TransitRepositoryImp
    driver_fee_service: DriverFeeService

    def __init__(
            self,
            driver_repository: DriverRepositoryImp = Depends(DriverRepositoryImp),
            driver_attribute_repository: DriverAttributeRepositoryImp = Depends(DriverAttributeRepositoryImp),
            transit_repository: TransitRepositoryImp = Depends(TransitRepositoryImp),
            driver_fee_service: DriverFeeService = Depends(DriverFeeService),
    ):
        self.driver_repository = driver_repository
        self.driver_attribute_repository = driver_attribute_repository
        self.transit_repository = transit_repository
        self.driver_fee_service = driver_fee_service

    def create_driver(
            self,
            license: str,
            last_name: str,
            first_name: str,
            a_type: Driver.Type,
            status: Driver.Status,
            photo: str,
    ) -> Driver:
        driver = Driver()
        if status == Driver.Status.ACTIVE:
            license_regexp = re.compile(self.DRIVER_LICENSE_REGEX)
            if license is None or license == "" or not license_regexp.match(license):
                raise AttributeError("Illegal license no = " + str(license))
        driver.driver_license = license
        driver.last_name = last_name
        driver.first_name = first_name
        driver.status = status
        driver.type = a_type
        if photo is not None and photo != "":
            if is_base_64(photo):
                driver.photo = photo
            else:
                raise AttributeError("Illegal photo in base64")
        return self.driver_repository.save(driver)

    def change_license_number(self, new_license: str, driver_id: int) -> None:
        driver = self.driver_repository.get_one(driver_id)
        if driver is None:
            raise AttributeError("Driver does not exists, id = " + str(driver_id))
        license_regexp = re.compile(self.DRIVER_LICENSE_REGEX)
        if new_license is None or new_license == "" or not license_regexp.match(new_license):
            raise AttributeError("Illegal license no = " + str(new_license))
        if not driver.status == Driver.Status.ACTIVE:
            raise AttributeError("Driver is not active, cannot change license")

        driver.driver_license = new_license
        self.driver_repository.save(driver)

    def change_driver_status(self, driver_id: int, status: Driver.Status) -> None:
        driver = self.driver_repository.get_one(driver_id)
        if driver is None:
            raise AttributeError("Driver does not exists, id = " + str(driver_id))
        if status == Driver.Status.ACTIVE:
            license = driver.driver_license
            license_regexp = re.compile(self.DRIVER_LICENSE_REGEX)
            if license is None or license == "" or not license_regexp.match(license):
                raise AttributeError("Status cannot be ACTIVE. Illegal license no = " + str(license))
        driver.status = status
        self.driver_repository.save(driver)

    def change_photo(self, driver_id: int, photo: str) -> None:
        driver = self.driver_repository.get_one(driver_id)
        if driver is None:
            raise AttributeError("Driver does not exists, id = " + str(driver_id))
        if photo is not None and photo != "":
            if is_base_64(photo):
                driver.photo = photo
            else:
                raise AttributeError("Illegal photo in base64")
        driver.photo = photo
        self.driver_repository.save(driver)

    def calculate_driver_monthly_payment(self, driver_id: int, year: int, month: int) -> int:
        driver = self.driver_repository.get_one(driver_id)
        if driver is None:
            raise AttributeError("Driver does not exists, id = " + str(driver_id))

        from_date = datetime(year, month, 1)
        to_date = datetime(year, month, calendar.monthrange(year, month)[1])

        transit_list = self.transit_repository.find_all_by_driver_and_date_time_between(driver_id, from_date, to_date)

        sum = reduce(lambda a, b: a + b, map(self.driver_fee_service.calculate_driver_fee, transit_list))

        return sum

    def calculate_driver_yearly_payment(self, driver_id: int, year: int) -> Dict[int, int]:
        payments = {}
        for m in range(1, 13):
            payments[m] = self.calculate_driver_monthly_payment(driver_id, year, m)
        return payments

    def load_driver(self, driver_id: int) -> DriverDTO:
        driver = self.driver_repository.get_one(driver_id)
        if driver is None:
            raise AttributeError("Driver does not exists, id = " + str(driver_id))
        return DriverDTO(**driver.dict())

    def add_attribute(self, driver_id: int, attr: DriverAttribute.DriverAttributeName, value: str) -> None:
        driver = self.driver_repository.get_one(driver_id)
        if driver is None:
            raise AttributeError("Driver does not exists, id = " + str(driver_id))
        self.driver_attribute_repository.save(DriverAttribute(driver=driver, name=attr, value=value))
