from datetime import datetime
from unittest import TestCase

from geolocation.distance import Distance
from money import Money
from pricing.tariff import Tariff
from ride.request_for_transit import RequestForTransit


class TestCalculateTransitPrice(TestCase):
    def test_calculate_price_on_regular_day(self) -> None:
        # given
        # friday
        request_for_transit: RequestForTransit = self.transit_was_on_done_on_friday(Distance.of_km(20))
        # when
        price: Money = request_for_transit.get_estimated_price()

        # then
        self.assertEqual(Money(2900), price)  # 29.00

    def test_calculate_price_on_sunday(self) -> None:
        # given
        request_for_transit: RequestForTransit = self.transit_was_done_on_sunday(Distance.of_km(20))

        # when
        price: Money = request_for_transit.get_estimated_price()

        # then
        self.assertEqual(Money(3800), price)  # 38.00

    def test_calculate_price_on_new_years_eve(self) -> None:
        # given
        request_for_transit: RequestForTransit = self.transit_was_done_on_new_years_eve(Distance.of_km(20))

        # when
        price: Money = request_for_transit.get_estimated_price()

        # then
        self.assertEqual(Money(8100), price)  # 81.00

    def test_calculate_price_on_saturday(self) -> None:
        # given
        request_for_transit: RequestForTransit = self.transit_was_done_on_saturday(Distance.of_km(20))

        # when
        price: Money = request_for_transit.get_estimated_price()

        # then
        self.assertEqual(Money(3800), price)  # 38.00

    def test_calculate_price_on_saturday_night(self) -> None:
        # given
        request_for_transit: RequestForTransit = self.transit_was_done_on_saturday_night(Distance.of_km(20))

        # when
        price: Money = request_for_transit.get_estimated_price()

        # then
        self.assertEqual(Money(6000), price)  # 60.00

    def transit_was_on_done_on_friday(self, distance: Distance) -> RequestForTransit:
        tariff: Tariff = Tariff.of_time(datetime(2021, 4, 16, 8, 30))
        request_for_transit: RequestForTransit = RequestForTransit(tariff=tariff, distance=distance)
        return request_for_transit

    def transit_was_done_on_new_years_eve(self, distance: Distance) -> RequestForTransit:
        tariff: Tariff = Tariff.of_time(datetime(2021, 12, 31, 8, 30))
        request_for_transit: RequestForTransit = RequestForTransit(tariff=tariff, distance=distance)
        return request_for_transit

    def transit_was_done_on_saturday(self, distance: Distance) -> RequestForTransit:
        tariff: Tariff = Tariff.of_time(datetime(2021, 4, 17, 8, 30))
        request_for_transit: RequestForTransit = RequestForTransit(tariff=tariff, distance=distance)
        return request_for_transit

    def transit_was_done_on_sunday(self, distance: Distance) -> RequestForTransit:
        tariff: Tariff = Tariff.of_time(datetime(2021, 4, 18, 8, 30))
        request_for_transit: RequestForTransit = RequestForTransit(tariff=tariff, distance=distance)
        return request_for_transit

    def transit_was_done_on_saturday_night(self, distance: Distance) -> RequestForTransit:
        tariff: Tariff = Tariff.of_time(datetime(2021, 4, 17, 19, 30))
        request_for_transit: RequestForTransit = RequestForTransit(tariff=tariff, distance=distance)
        return request_for_transit
