from datetime import datetime
from unittest import TestCase

from entity import Transit


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
        price: int = transit.calculate_final_costs()

        self.assertEqual(2900, price)

    def test_estimate_price_on_regular_day(self):
        # given
        transit: Transit = self.transit(Transit.Status.DRAFT, 20)

        # friday
        self.transit_was_on_done_on_friday(transit)
        # when
        price: int = transit.estimate_cost()

        # then
        self.assertEqual(2900, price)

    def transit(self, status: Transit.Status, km: int) -> Transit:
        transit = Transit()
        transit.date_time = datetime.now()
        transit.status = Transit.Status.DRAFT
        transit.set_km(km)
        transit.status = status
        return transit

    def transit_was_on_done_on_friday(self, transit: Transit) -> None:
        transit.date_time = datetime(2021, 4, 16, 8, 30)
