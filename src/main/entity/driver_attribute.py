from enum import Enum

from entity import Driver


class DriverAttribute:
    class DriverAttributeName(Enum):
        PENALTY_POINTS = 1
        NATIONALITY = 2
        YEARS_OF_EXPERIENCE = 3
        MEDICAL_EXAMINATION_EXPIRATION_DATE = 4
        MEDICAL_EXAMINATION_REMARKS = 5
        EMAIL = 6
        BIRTHPLACE = 7
        COMPANY_NAME = 8

    _id: int
    name: DriverAttributeName
    value: str
    driver: Driver

    def __init__(self, driver: Driver, attr: DriverAttributeName, value: str):
        self.driver = driver
        self.value = value
        self.name = attr
