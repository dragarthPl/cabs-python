from entity import DriverFee
from fastapi import Depends

from money import Money
from repository.driver_fee_repository import DriverFeeRepositoryImp
from repository.transit_repository import TransitRepositoryImp


class DriverFeeService:
    driver_fee_repository: DriverFeeRepositoryImp
    transit_repository: TransitRepositoryImp

    def __init__(
            self,
            driver_fee_repository: DriverFeeRepositoryImp = Depends(DriverFeeRepositoryImp),
            transit_repository: TransitRepositoryImp = Depends(TransitRepositoryImp),
    ):
        self.driver_fee_repository = driver_fee_repository
        self.transit_repository = transit_repository

    def calculate_driver_fee(self, transit_id: int) -> Money:
        transit = self.transit_repository.get_one(transit_id)
        if transit is None:
            raise AttributeError("transit does not exist, id = " + str(transit_id))
        if transit.drivers_fee:
            return transit.get_drivers_fee()
        transit_price: Money = transit.get_price()
        driver_fee = self.driver_fee_repository.find_by_driver(transit.driver)
        if driver_fee is None:
            raise AttributeError("driver Fees not defined for driver, driver id = " + str(transit.driver.id))
        final_fee = None
        if driver_fee.fee_type == DriverFee.FeeType.FLAT:
            final_fee = transit_price.subtract(Money(driver_fee.amount))
        else:
            final_fee = transit_price.percentage(driver_fee.amount)

        return Money(max(final_fee.to_int(), 0 if not driver_fee.min else driver_fee.min))
