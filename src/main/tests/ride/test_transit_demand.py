from unittest import TestCase

from common.base_entity import new_uuid
from ride.transit_demand import TransitDemand


class TestTransitDemand(TestCase):
    def test_can_change_pickup_place(self):
        # given
        transit_demand: TransitDemand = self.transit_demand()

        # expect
        transit_demand.change_pickup(0.2)

    def test_cannot_change_pickup_place_after_transit_is_accepted(self):
        # given
        transit_demand: TransitDemand = self.transit_demand()
        # and
        transit_demand.accept()

        # expect
        with self.assertRaises(AttributeError):
            transit_demand.change_pickup(0.1)
        # and
        # expect
        with self.assertRaises(AttributeError):
            transit_demand.change_pickup(0.11)

    def test_cannot_change_pickup_place_more_than_three_times(self):
        # given
        transit_demand: TransitDemand = self.transit_demand()
        # and
        transit_demand.change_pickup(0.1)
        # and
        transit_demand.change_pickup(0.2)
        # and
        transit_demand.change_pickup(0.22)

        # expect
        with self.assertRaises(AttributeError):
            transit_demand.change_pickup(0.23)

    def test_cannot_change_pickup_place_when_it_is_far_way_from_original(self):
        # given
        transit_demand: TransitDemand = self.transit_demand()

        # expect
        with self.assertRaises(AttributeError):
            transit_demand.change_pickup(50)

    def test_can_cancel_demand(self):
        # given
        transit_demand: TransitDemand = self.transit_demand()

        # when
        transit_demand.cancel()

        # then
        self.assertEqual(TransitDemand.Status.CANCELLED, transit_demand.status)

    def test_can_publish_demand(self):
        # given
        transit_demand: TransitDemand = self.transit_demand()

        # then
        self.assertEqual(TransitDemand.Status.WAITING_FOR_DRIVER_ASSIGNMENT, transit_demand.status)

    def transit_demand(self) -> TransitDemand:
        return TransitDemand(new_uuid())
