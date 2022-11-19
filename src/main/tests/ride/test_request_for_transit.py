from datetime import datetime
from unittest import TestCase

from geolocation.distance import Distance
from pricing.tariff import Tariff
from ride.request_for_transit import RequestForTransit


class TestRequestForTransit(TestCase):
    def test_can_create_request_for_transit(self):
        # when
        request_for_transit: RequestForTransit = self.request_transit()

        # expect
        self.assertIsNotNone(request_for_transit.get_tariff())
        self.assertNotEquals(0, request_for_transit.get_tariff().km_rate)

    def request_transit(self) -> RequestForTransit:
        tariff: Tariff = Tariff.of_time(datetime.now())
        return RequestForTransit(tariff=tariff, distance=Distance.ZERO)
