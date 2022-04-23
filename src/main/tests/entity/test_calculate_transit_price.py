from datetime import datetime
from unittest import TestCase

import pytz

from distance.distance import Distance
from entity import Transit
from money import Money


class TestCalculateTransitPrice(TestCase):

    def test_cannot_calculate_price_when_transit_is_cancelled(self):
        # given
        transit: Transit = self.transit(Transit.Status.CANCELLED, 20)

        # when
        with self.assertRaises(ValueError):
            transit.calculate_final_costs()

    def test_cannot_estimate_price_when_transit_is_completed(self):
        # given
        transit: Transit = self.transit(Transit.Status.COMPLETED, 20)

        # when
        with self.assertRaises(ValueError):
            transit.estimate_cost()

    def test_calculate_price_on_regular_day(self):
        # given
        transit: Transit = self.transit(Transit.Status.COMPLETED, 20)

        # friday
        self.transit_was_on_done_on_friday(transit)
        # when
        price: Money = transit.calculate_final_costs()

        self.assertEqual(Money(2900), price)

    def test_calculate_price_on_sunday(self):
        # given
        transit: Transit = self.transit(Transit.Status.COMPLETED, 20)
        # and
        self.transit_was_done_on_sunday(transit)

        # when
        price: Money = transit.calculate_final_costs()
        print(price.to_string())

        self.assertEqual(Money(3800), price)

    def test_calculate_price_on_new_years_eve(self):
        # given
        transit: Transit = self.transit(Transit.Status.COMPLETED, 20)
        # and
        self.transit_was_done_on_new_years_eve(transit)

        # when
        price: Money = transit.calculate_final_costs()

        # then
        self.assertEqual(Money(8100), price)

    def test_calculate_price_on_saturday(self):
        # given
        transit: Transit = self.transit(Transit.Status.COMPLETED, 20)
        # and
        self.transit_was_done_on_saturday(transit)

        # when
        price: Money = transit.calculate_final_costs()

        # then
        self.assertEqual(Money(3800), price)

    def test_calculate_price_on_saturday_night(self):
        # given
        transit: Transit = self.transit(Transit.Status.COMPLETED, 20)

        # friday
        self.transit_was_done_on_saturday_night(transit)
        # when
        price: Money = transit.calculate_final_costs()

        # then
        self.assertEqual(Money(6000), price)


    def test_estimate_price_on_regular_day(self):
        # given
        transit: Transit = self.transit(Transit.Status.DRAFT, 20)

        # friday
        self.transit_was_on_done_on_friday(transit)
        # when
        price: Money = transit.estimate_cost()

        # then
        self.assertEqual(Money(2900), price)

    def transit(self, status: Transit.Status, km: int) -> Transit:
        transit = Transit()
        transit.set_date_time(datetime.now())
        transit.status = Transit.Status.DRAFT
        transit.set_km(Distance.of_km(km))
        transit.status = status
        return transit

    def transit_was_on_done_on_friday(self, transit: Transit) -> None:
        transit.set_date_time(datetime(2021, 4, 16, 8, 30).astimezone(pytz.utc))

    def transit_was_done_on_new_years_eve(self, transit: Transit) -> None:
        transit.set_date_time(datetime(2021, 12, 31, 8, 30).astimezone(pytz.utc))

    def transit_was_done_on_saturday(self, transit: Transit) -> None:
        transit.set_date_time(datetime(2021, 4, 17, 8, 30).astimezone(pytz.utc))

    def transit_was_done_on_sunday(self, transit: Transit) -> None:
        transit.set_date_time(datetime(2021, 4, 18, 8, 30).astimezone(pytz.utc))

    def transit_was_done_on_saturday_night(self, transit: Transit) -> None:
        transit.set_date_time(datetime(2021, 4, 17, 19, 30).astimezone(pytz.utc))

    def transit_was_done_in_2018(self, transit):
        transit.set_date_time(datetime(2018, 1,1, 8, 30).astimezone(pytz.utc))
