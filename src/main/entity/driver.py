from decimal import Decimal
from enum import Enum
from typing import Set

from common.base_entity import BaseEntity
from entity import Transit


class Driver(BaseEntity, table=True):
    class Type(Enum):
        CANDIDATE = 1
        REGULAR = 2

    class Status(Enum):
        ACTIVE = 1
        INACTIVE = 2

    _type: Type
    status: Status

    first_name: str
    last_name: str
    photo: str

    driver_license: str
    fee: 'DriverFee'

    is_occupied: bool
    attributes: Set[DriverAttribute]
    transits: Set[Transit]

    def calculate_earnings_for_transit(self, transit: Transit) -> Decimal:
        pass


