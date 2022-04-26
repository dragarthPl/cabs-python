from datetime import datetime
from unittest import TestCase

from distance.distance import Distance
from dto.transit_dto import TransitDTO
from entity import Transit, Address, Client
from money import Money


class TestCalculateTransitDistance(TestCase):
    def test_should_not_work_with_invalid_unit(self):
        with self.assertRaises(AttributeError):
            self.transit_for_distance(2.00).get_distance("invalid")

    def test_should_represent_as_km(self):
        self.assertEqual("10km", self.transit_for_distance(10).get_distance("km"))
        self.assertEqual("10.123km", self.transit_for_distance(10.123).get_distance("km"))
        self.assertEqual("10.123km", self.transit_for_distance(10.12345).get_distance("km"))
        self.assertEqual("0km", self.transit_for_distance(0).get_distance("km"))

    def test_should_represent_as_meters(self):
        self.assertEqual("10000m", self.transit_for_distance(10).get_distance("m"))
        self.assertEqual("10123m", self.transit_for_distance(10.123).get_distance("m"))
        self.assertEqual("10123m", self.transit_for_distance(10.12345).get_distance("m"))
        self.assertEqual("0m", self.transit_for_distance(0).get_distance("m"))

    def test_should_represent_as_miles(self):
        self.assertEqual("6.214miles", self.transit_for_distance(10).get_distance("miles"))
        self.assertEqual("6.290miles", self.transit_for_distance(10.123).get_distance("miles"))
        self.assertEqual("6.290miles", self.transit_for_distance(10.12345).get_distance("miles"))
        self.assertEqual("0miles", self.transit_for_distance(0).get_distance("miles"))

    def transit_for_distance(self, km: float) -> TransitDTO:
        t: Transit = Transit()
        t.set_price(Money(10))
        t.set_date_time(datetime.now())
        t.address_to = Address()
        t.address_from = Address()
        t.status = Transit.Status.DRAFT
        t.set_km(Distance.of_km(km))
        t.client = Client()
        return TransitDTO(transit=t)
