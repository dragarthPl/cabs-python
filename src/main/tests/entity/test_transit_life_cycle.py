from datetime import datetime
from unittest import TestCase

from geolocation.distance import Distance
from entity import Transit, Address


class TestTransitLifeCycle(TestCase):
    DRIVER_ID: int = 1
    SECOND_DRIVER_ID: int = 2
    
    def test_can_create_transit(self):
        # when
        transit = self.request_transit()

        # then
        self.assertEqual(0, transit.get_price().to_int())
        self.assertEqual(Transit.Status.DRAFT, transit.status)
        self.assertIsNotNone(transit.get_tariff())
        self.assertNotEqual(0, transit.get_tariff().km_rate)

    def test_can_change_transit_destination(self):
        # given
        transit = self.request_transit()

        # when
        transit.change_destination_to(
            Address(country="Polska", city="Warszawa", street="Mazowiecka", building_number=30),
            Distance.of_km(20)
        )

        # then
        self.assertIsNotNone(transit.estimated_price)
        self.assertIsNone(transit.get_price().to_int())

    def test_cannot_change_destination_when_transit_is_completed(self):
        # given
        destination = Address(country="Polska", city="Warszawa", street="Żytnia", building_number=25)
        # and
        transit = self.request_transit()
        # and
        transit.publish_at(datetime.now())
        # and
        transit.propose_to(self.DRIVER_ID)
        # and
        transit.accept_by(self.DRIVER_ID, datetime.now())
        # and
        transit.start(datetime.now())
        # and
        transit.complete_ride_at(datetime.now(), destination, Distance.of_km(20))

        # expect
        with self.assertRaises(AttributeError):
            transit.change_destination_to(
                Address(country="Polska", city="Warszawa", street="Żytnia", building_number=23),
                Distance.of_km(20),
            )

    def test_can_change_pickup_place(self):
        # given
        transit = self.request_transit()

        # expect
        transit.change_pickup_to(
            Address(country="Polska", city="Warszawa", street="Puławska", building_number=28),
            Distance.of_km(20),
            0.2
        )

    def test_cannot_change_pickup_place_after_transit_is_accepted(self):
        # given
        destination = Address(country="Polska", city="Warszawa", street="Żytnia", building_number=25)
        # and
        transit = self.request_transit()
        # and
        changed_to = Address(country="Polska", city="Warszawa", street="Żytnia", building_number=27)
        # and
        transit.publish_at(datetime.now())
        # and
        transit.propose_to(self.DRIVER_ID)
        # and
        transit.accept_by(self.DRIVER_ID, datetime.now())

        # expect
        with self.assertRaises(AttributeError):
            transit.change_pickup_to(changed_to, Distance.of_km(20.1), 0.1)

        # and
        transit.start(datetime.now())
        # expect
        with self.assertRaises(AttributeError):
            transit.change_pickup_to(changed_to, Distance.of_km(20.11), 0.11)

        # and
        transit.complete_ride_at(datetime.now(), destination, Distance.of_km(20.12))
        # expect
        with self.assertRaises(AttributeError):
            transit.change_pickup_to(changed_to, Distance.of_km(20.12), 0.12)

    def test_cannot_change_pickup_place_more_than_three_times(self):
        # given
        transit = self.request_transit()
        # and
        transit.change_pickup_to(
            Address(country="Polska", city="Warszawa", street="Żytnia", building_number=26),
            Distance.of_km(20.1),
            0.1
        )
        # and
        transit.change_pickup_to(
            Address(country="Polska", city="Warszawa", street="Żytnia", building_number=27),
            Distance.of_km(20.2),
            0.2
        )
        # and
        transit.change_pickup_to(
            Address(country="Polska", city="Warszawa", street="Żytnia", building_number=28),
            Distance.of_km(20.22),
            0.22
        )

        # expect
        with self.assertRaises(AttributeError):
            transit.change_pickup_to(
                Address(country="Polska", city="Warszawa", street="Żytnia", building_number=29),
                Distance.of_km(20.3),
                0.23
            )

    def test_cannot_change_pickup_place_when_it_is_far_way_from_original(self):
        # given
        transit = self.request_transit()

        # expect
        with self.assertRaises(AttributeError):
            transit.change_pickup_to(
                Address(),
                Distance.of_km(20),
                50
            )

    def test_can_cancel_transit(self):
        # given
        transit = self.request_transit()

        # when
        transit.cancel()

        # then
        self.assertEqual(Transit.Status.CANCELLED, transit.status)

    def test_cannot_cancel_transit_after_it_was_started(self):
        # given
        destination = Address(country="Polska", city="Warszawa", street="Żytnia", building_number=25)
        # and
        transit = self.request_transit()
        # and
        transit.publish_at(datetime.now())
        # and
        transit.propose_to(self.DRIVER_ID)
        # and
        transit.accept_by(self.DRIVER_ID, datetime.now())

        # and
        transit.start(datetime.now())
        # expect
        with self.assertRaises(AttributeError):
            transit.cancel()

        # and
        transit.complete_ride_at(datetime.now(), destination, Distance.of_km(20))
        # expect
        with self.assertRaises(AttributeError):
            transit.cancel()

    def test_can_publish_transit(self):
        transit = self.request_transit()

        # when
        transit.publish_at(datetime.now())

        # then
        self.assertEqual(Transit.Status.WAITING_FOR_DRIVER_ASSIGNMENT, transit.status)
        self.assertIsNotNone(transit.published)

    def test_can_accept_transit(self):
        # given
        transit = self.request_transit()
        # and
        transit.publish_at(datetime.now())
        # and
        transit.propose_to(self.DRIVER_ID)

        # when
        transit.accept_by(self.DRIVER_ID, datetime.now())

        # then
        self.assertEqual(Transit.Status.TRANSIT_TO_PASSENGER, transit.status)

    def test_only_one_driver_can_accept_transit(self):
        # given
        transit = self.request_transit()
        # and
        transit.publish_at(datetime.now())
        # and
        transit.propose_to(self.DRIVER_ID)
        # and
        transit.accept_by(self.DRIVER_ID, datetime.now())

        with self.assertRaises(AttributeError):
            transit.accept_by(self.SECOND_DRIVER_ID, datetime.now())

    def test_transit_cannot_by_accepted_by_driver_who_already_rejected(self):
        # given
        transit = self.request_transit()
        # and
        transit.publish_at(datetime.now())
        # and
        transit.reject_by(self.DRIVER_ID)

        # when
        with self.assertRaises(AttributeError):
            transit.accept_by(self.DRIVER_ID, datetime.now())

    def test_transit_cannot_by_accepted_by_driver_who_has_not_seen_proposal(self):
        # given
        transit = self.request_transit()
        # and
        transit.publish_at(datetime.now())

        # when
        with self.assertRaises(AttributeError):
            transit.accept_by(self.DRIVER_ID, datetime.now())

    def test_can_start_transit(self):
        # given
        transit = self.request_transit()
        # and
        transit.publish_at(datetime.now())
        # and
        transit.propose_to(self.DRIVER_ID)
        # and
        transit.accept_by(self.DRIVER_ID, datetime.now())

        # when
        transit.start(datetime.now())

        # then
        self.assertEqual(Transit.Status.IN_TRANSIT, transit.status)

    def test_cannot_start_not_accepted_transit(self):
        # given
        transit = self.request_transit()
        # and
        transit.publish_at(datetime.now())

        # when
        with self.assertRaises(AttributeError):
            transit.start(datetime.now())

    def test_can_complete_transit(self):
        # given
        destination = Address(country="Polska", city="Warszawa", street="Żytnia", building_number=25)
        # and
        transit = self.request_transit()
        # and
        transit.publish_at(datetime.now())
        # and
        transit.propose_to(self.DRIVER_ID)
        # and
        transit.accept_by(self.DRIVER_ID, datetime.now())
        # and
        transit.start(datetime.now())

        # when
        transit.complete_ride_at(datetime.now(), destination, Distance.of_km(20))

        # then
        self.assertEqual(Transit.Status.COMPLETED, transit.status)
        self.assertIsNotNone(transit.get_tariff())
        self.assertIsNotNone(transit.get_price())

    def test_cannot_complete_not_started_transit(self):
        # given
        address_to = Address(country="Polska", city="Warszawa", street="Żytnia", building_number=25)
        # and
        transit = self.request_transit()
        # and
        transit.publish_at(datetime.now())
        # and
        transit.propose_to(self.DRIVER_ID)
        # and
        transit.accept_by(self.DRIVER_ID, datetime.now())

        # when
        with self.assertRaises(AttributeError):
            transit.complete_ride_at(datetime.now(), address_to, Distance.of_km(20))

    def test_can_reject_transit(self):
        # given
        transit = self.request_transit()
        # and
        transit.publish_at(datetime.now())

        # when
        transit.reject_by(self.DRIVER_ID)

        # then
        self.assertEqual(Transit.Status.WAITING_FOR_DRIVER_ASSIGNMENT, transit.status)

    def request_transit(self) -> Transit:
        return Transit(
            when=datetime.now(),
            distance=Distance.ZERO,
        )

