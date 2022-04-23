from unittest import TestCase

from distance.distance import Distance


class TestDistance(TestCase):

    def test_cannot_understand_invalid_unit(self):
        with self.assertRaises(AttributeError):
            Distance.of_km(2000).print_in("invalid")

    def test_can_convert_to_float(self):
        # expect
        self.assertEqual(2000.0, Distance.of_km(2000).to_km_in_float())
        self.assertEqual(0.0, Distance.of_km(0).to_km_in_float())
        self.assertEqual(312.22, Distance.of_km(312.22).to_km_in_float())
        self.assertEqual(2, Distance.of_km(2).to_km_in_float())

    def test_can_represent_distance_as_meters(self):
        # expect
        self.assertEqual("2000000m", Distance.of_km(2000).print_in("m"))
        self.assertEqual("0m", Distance.of_km(0).print_in("m"))
        self.assertEqual("312220m", Distance.of_km(312.22).print_in("m"))
        self.assertEqual("2000m", Distance.of_km(2).print_in("m"))

    def test_can_represent_distance_as_km(self):
        # expect
        self.assertEqual("2000km", Distance.of_km(2000).print_in("km"))
        self.assertEqual("0km", Distance.of_km(0).print_in("km"))
        self.assertEqual("312.220km", Distance.of_km(312.22).print_in("km"))
        self.assertEqual("312.221km", Distance.of_km(312.221111232313).print_in("km"))
        self.assertEqual("2km", Distance.of_km(2).print_in("km"))

    def test_can_represent_distance_as_miles(self):
        # expect
        self.assertEqual("1242.742miles", Distance.of_km(2000).print_in("miles"))
        self.assertEqual("0miles", Distance.of_km(0).print_in("miles"))
        self.assertEqual("194.005miles", Distance.of_km(312.22).print_in("miles"))
        self.assertEqual("194.005miles", Distance.of_km(312.221111232313).print_in("miles"))
        self.assertEqual("1.243miles", Distance.of_km(2).print_in("miles"))

