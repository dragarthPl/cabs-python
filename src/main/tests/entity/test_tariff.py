from datetime import datetime
from unittest import TestCase

from distance.distance import Distance
from entity import Tariff
from money import Money


class TestTariff(TestCase):
    def test_regular_tariff_should_be_displayed_and_calculated(self):
        # Given
        tariff = Tariff.of_time(datetime(2021, 4, 16, 8, 30))

        # expect
        self.assertEqual(Money(2900), tariff.calculate_cost(Distance.of_km(20)))
        self.assertEqual("Standard", tariff.name)
        self.assertEqual(1.0, tariff.km_rate)

    def test_sunday_tariff_should_be_displayed_and_calculated(self):
        # Given
        tariff = Tariff.of_time(datetime(2021, 4, 18, 8, 30))

        # expect
        self.assertEqual(Money(3800), tariff.calculate_cost(Distance.of_km(20)))
        self.assertEqual("Weekend", tariff.name)
        self.assertEqual(1.5, tariff.km_rate)

    def test_new_years_eve_tariff_should_be_displayed_and_calculated(self):
        # Given
        tariff = Tariff.of_time(datetime(2021, 12, 31, 8, 30))

        # expect
        self.assertEqual(Money(8100), tariff.calculate_cost(Distance.of_km(20)))
        self.assertEqual("Sylwester", tariff.name)
        self.assertEqual(3.5, tariff.km_rate)

    def test_saturday_tariff_should_be_displayed_and_calculated(self):
        # Given
        tariff = Tariff.of_time(datetime(2021, 4, 17, 8, 30))

        # expect
        self.assertEqual(Money(3800), tariff.calculate_cost(Distance.of_km(20)))
        self.assertEqual("Weekend", tariff.name)
        self.assertEqual(1.5, tariff.km_rate)

    def test_saturday_night_tariff_should_be_displayed_and_calculated(self):
        # Given
        tariff = Tariff.of_time(datetime(2021, 4, 17, 19, 30))

        # expect
        self.assertEqual(Money(6000), tariff.calculate_cost(Distance.of_km(20)))
        self.assertEqual("Weekend+", tariff.name)
        self.assertEqual(2.5, tariff.km_rate)
