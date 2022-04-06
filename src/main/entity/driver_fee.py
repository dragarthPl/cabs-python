from enum import Enum

from src.main.common.base_entity import BaseEntity
from entity.driver import Driver


class DriverFee(BaseEntity, table=True):
    class FeeType(Enum):
        FLAT = 1
        PERCENTAGE = 2

    fee_type: FeeType
    driver: 'Driver'
    amount: int
    min_amount: int

    def __init__(self, fee_type: FeeType, driver: Driver, amount: int, min_amount: int):
        self.feeType = fee_type
        self.driver = driver
        self.amount = amount
        self.min_amount = min_amount
