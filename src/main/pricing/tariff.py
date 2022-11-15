import calendar
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

from geolocation.distance import Distance
from money import Money


class Tariff:
    BASE_FEE: int = 8
    km_rate: float
    name: str
    base_fee: int

    def __init__(self, km_rate: float, name: str, base_fee: int):
        self.name = name
        self.km_rate = km_rate
        self.base_fee = base_fee

    @classmethod
    def of_time(cls, time: datetime) -> 'Tariff':
        if (time.month == 12 and time.day == 31) or (time.month == 1 and time.day == 1 and time.hour <= 6):
            return Tariff(3.50, "Sylwester", cls.BASE_FEE + 3)
        else:
            # piątek i sobota po 17 do 6 następnego dnia
            if ((time.weekday() == calendar.FRIDAY and time.hour >= 17) or
                    (time.weekday() == calendar.SATURDAY and time.hour <= 6) or
                    (time.weekday() == calendar.SATURDAY and time.hour >= 17) or
                    (time.weekday() == calendar.SUNDAY and time.hour <= 6)):
                return Tariff(2.5, "Weekend+", cls.BASE_FEE + 2)
            else:
                # pozostałe godziny weekendu
                if (time.weekday() == calendar.SATURDAY and 6 < time.hour < 17) or (
                        time.weekday() == calendar.SUNDAY and time.hour > 6):
                    return Tariff(1.5, "Weekend", cls.BASE_FEE)
                else:
                    # tydzień roboczy
                    return Tariff(1.0, "Standard", cls.BASE_FEE + 1)

    def calculate_cost(self, distance: Distance) -> Money:
        price_big_decimal: Decimal = Decimal(
            distance.to_km_in_float() * self.km_rate + self.base_fee
        ).quantize(Decimal('.01'), rounding=ROUND_HALF_UP)
        final_price: int = int(str(price_big_decimal).replace(".", ""))
        return Money(final_price)
