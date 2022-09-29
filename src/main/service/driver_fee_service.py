from typing import Optional

from entity import DriverFee
from fastapi import Depends

from money import Money
from repository.driver_fee_repository import DriverFeeRepositoryImp


class DriverFeeService:
    driver_fee_repository: DriverFeeRepositoryImp

    def __init__(
            self,
            driver_fee_repository: DriverFeeRepositoryImp = Depends(DriverFeeRepositoryImp),
    ):
        self.driver_fee_repository = driver_fee_repository

    def calculate_driver_fee(self, transit_price: Money, driver_id: int) -> Money:
        driver_fee: DriverFee = self.driver_fee_repository.find_by_driver_id(driver_id)
        if driver_id is None:
            raise AttributeError("driver Fees not defined for driver, driver id = " + str(driver_id))
        final_fee: Optional[Money] = None
        if driver_fee.fee_type == DriverFee.FeeType.FLAT:
            final_fee = transit_price.subtract(Money(driver_fee.amount))
        else:
            final_fee = transit_price.percentage(driver_fee.amount)

        return Money(max(final_fee.to_int(), 0 if not driver_fee.min else driver_fee.min))
