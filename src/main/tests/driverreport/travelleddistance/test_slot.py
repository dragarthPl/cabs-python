from datetime import datetime
from unittest import TestCase

import pytz
from dateutil.relativedelta import relativedelta

from driverreport.travelleddistance.travelled_distance import TimeSlot


class TestSlot(TestCase):
    NOON = datetime(1989, 12, 12, 12, 10).astimezone(pytz.utc)
    NOON_FIVE = NOON + relativedelta(minutes=5)
    NOON_TEN = NOON_FIVE + relativedelta(minutes=5)

    def test_beginning_must_be_before_end(self):
        # expect
        with self.assertRaises(ValueError):
            TimeSlot.of(self.NOON_FIVE, self.NOON)
        with self.assertRaises(ValueError):
            TimeSlot.of(self.NOON_TEN, self.NOON)
        with self.assertRaises(ValueError):
            TimeSlot.of(self.NOON_TEN, self.NOON_FIVE)
        with self.assertRaises(ValueError):
            TimeSlot.of(self.NOON_TEN, self.NOON_TEN)

    def test_can_create_valid_slot(self):
        # given
        noon_to_five: TimeSlot = TimeSlot.of(self.NOON, self.NOON_FIVE)
        five_to_ten: TimeSlot = TimeSlot.of(self.NOON_FIVE, self.NOON_TEN)

        # expect
        self.assertEqual(self.NOON, noon_to_five.beginning)
        self.assertEqual(self.NOON_FIVE, noon_to_five.end)
        self.assertEqual(self.NOON_FIVE, five_to_ten.beginning)
        self.assertEqual(self.NOON_TEN, five_to_ten.end)

    def test_can_create_previous_slot(self):
        # given
        noon_to_five: TimeSlot = TimeSlot.of(self.NOON, self.NOON_FIVE)
        five_to_ten: TimeSlot = TimeSlot.of(self.NOON_FIVE, self.NOON_TEN)
        ten_to_fifteen: TimeSlot = TimeSlot.of(self.NOON_TEN, self.NOON_TEN + relativedelta(minutes=5))

        # expect
        self.assertEqual(noon_to_five, five_to_ten.prev())
        self.assertEqual(five_to_ten, ten_to_fifteen.prev())
        self.assertEqual(noon_to_five, ten_to_fifteen.prev().prev())

    def test_can_calculate_if_timestamp_is_within(self):
        # given
        noon_to_five: TimeSlot = TimeSlot.of(self.NOON, self.NOON_FIVE)
        five_to_ten: TimeSlot = TimeSlot.of(self.NOON_FIVE, self.NOON_TEN)

        # expect
        self.assertTrue(noon_to_five.contains(self.NOON))
        self.assertTrue(noon_to_five.contains(self.NOON + relativedelta(minutes=1)))
        self.assertFalse(noon_to_five.contains(self.NOON_FIVE))
        self.assertFalse(noon_to_five.contains(self.NOON_FIVE + relativedelta(minutes=1)))

        self.assertFalse(noon_to_five.is_before(self.NOON))
        self.assertFalse(noon_to_five.is_before(self.NOON_FIVE))
        self.assertTrue(noon_to_five.is_before(self.NOON_TEN))

        self.assertTrue(noon_to_five.ends_at(self.NOON_FIVE))

        self.assertFalse(five_to_ten.contains(self.NOON))
        self.assertTrue(five_to_ten.contains(self.NOON_FIVE))
        self.assertTrue(five_to_ten.contains(self.NOON_FIVE + relativedelta(minutes=1)))
        self.assertFalse(five_to_ten.contains(self.NOON_TEN))
        self.assertFalse(five_to_ten.contains(self.NOON_TEN + relativedelta(minutes=1)))

        self.assertFalse(five_to_ten.is_before(self.NOON))
        self.assertFalse(five_to_ten.is_before(self.NOON_FIVE))
        self.assertFalse(five_to_ten.is_before(self.NOON_TEN))
        self.assertTrue(five_to_ten.is_before(self.NOON_TEN + relativedelta(minutes=1)))

        self.assertTrue(five_to_ten.ends_at(self.NOON_TEN))

    def test_can_create_slot_from_seed_within_that_slot(self):
        # expect
        self.assertEqual(TimeSlot.of(self.NOON, self.NOON_FIVE), TimeSlot.slot_that_contains(
            self.NOON + relativedelta(minutes=1)))
        self.assertEqual(TimeSlot.of(self.NOON, self.NOON_FIVE), TimeSlot.slot_that_contains(
            self.NOON + relativedelta(minutes=2)))
        self.assertEqual(TimeSlot.of(self.NOON, self.NOON_FIVE), TimeSlot.slot_that_contains(
            self.NOON + relativedelta(minutes=3)))
        self.assertEqual(TimeSlot.of(self.NOON, self.NOON_FIVE), TimeSlot.slot_that_contains(
            self.NOON + relativedelta(minutes=4)))

        self.assertEqual(TimeSlot.of(self.NOON_FIVE, self.NOON_TEN), TimeSlot.slot_that_contains(
            self.NOON_FIVE + relativedelta(minutes=1)))
        self.assertEqual(TimeSlot.of(self.NOON_FIVE, self.NOON_TEN), TimeSlot.slot_that_contains(
            self.NOON_FIVE + relativedelta(minutes=2)))
        self.assertEqual(TimeSlot.of(self.NOON_FIVE, self.NOON_TEN), TimeSlot.slot_that_contains(
            self.NOON_FIVE + relativedelta(minutes=3)))
