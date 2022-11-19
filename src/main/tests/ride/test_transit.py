from datetime import datetime
from unittest import TestCase

from common.base_entity import new_uuid
from geolocation.distance import Distance
from pricing.tariff import Tariff
from ride.transit import Transit


class TestTransit(TestCase):

    def test_can_change_transit_destination(self):
        # given
        transit: Transit = self.transit()

        # expect
        transit.change_destination(Distance.of_km(20))

        # then
        self.assertEqual(Distance.of_km(20), transit.get_distance())

    def test_cannot_change_destination_when_transit_is_completed(self):
        # given
        transit: Transit = self.transit()
        # and
        transit.complete_ride_at(Distance.of_km(20))

        # expect
        with self.assertRaises(AttributeError):
            transit.change_destination(Distance.of_km(20))

    def test_can_complete_transit(self):
        transit: Transit = self.transit()
        # and
        transit.complete_ride_at(Distance.of_km(20))

        # then
        self.assertEqual(Transit.Status.COMPLETED, transit.status)

    def transit(self) -> Transit:
        return Transit(tariff=Tariff.of_time(datetime.now()), transit_request_uuid=new_uuid())
