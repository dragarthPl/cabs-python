from datetime import datetime
from unittest import TestCase

import pytz
from dateutil.relativedelta import relativedelta

from loyalty.constant_until import ConstantUntil
from loyalty.miles import Miles
from loyalty.two_step_expiring_miles import TwoStepExpiringMiles


class MilesTest(TestCase):
    YESTERDAY = datetime(1989, 12, 12, 12, 12).astimezone(pytz.utc)
    TODAY = YESTERDAY + relativedelta(days=1)
    TOMORROW = TODAY + relativedelta(days=1)

    def test_miles_without_expiration_date_dont_expire(self):
        # given
        never_expiring: Miles = ConstantUntil.constant_until_forever(10)

        # expect
        self.assertEqual(10, never_expiring.get_amount_for(self.YESTERDAY))
        self.assertEqual(10, never_expiring.get_amount_for(self.TODAY))
        self.assertEqual(10, never_expiring.get_amount_for(self.TOMORROW))

    def test_expiring_miles_expire(self):
        # given
        expiring: Miles = ConstantUntil.constant_until(10, self.TODAY)

        # expect
        self.assertEqual(10, expiring.get_amount_for(self.YESTERDAY))
        self.assertEqual(10, expiring.get_amount_for(self.TODAY))
        self.assertEqual(0, expiring.get_amount_for(self.TOMORROW))

    def test_can_subtract_when_enough_miles(self):
        # given
        expiring_miles: Miles = ConstantUntil.constant_until(10, self.TODAY)
        never_expiring: Miles = ConstantUntil.constant_until_forever(10)

        # expect
        self.assertEqual(ConstantUntil.constant_until(0, self.TODAY), expiring_miles.subtract(10, self.TODAY))
        self.assertEqual(ConstantUntil.constant_until(0, self.TODAY), expiring_miles.subtract(10, self.YESTERDAY))

        self.assertEqual(ConstantUntil.constant_until(2, self.TODAY), expiring_miles.subtract(8, self.TODAY))
        self.assertEqual(ConstantUntil.constant_until(2, self.TODAY), expiring_miles.subtract(8, self.YESTERDAY))

        self.assertEqual(ConstantUntil.constant_until_forever(0), never_expiring.subtract(10, self.YESTERDAY))
        self.assertEqual(ConstantUntil.constant_until_forever(0), never_expiring.subtract(10, self.TODAY))
        self.assertEqual(ConstantUntil.constant_until_forever(0), never_expiring.subtract(10, self.TOMORROW))

        self.assertEqual(ConstantUntil.constant_until_forever(2), never_expiring.subtract(8, self.YESTERDAY))
        self.assertEqual(ConstantUntil.constant_until_forever(2), never_expiring.subtract(8, self.TODAY))
        self.assertEqual(ConstantUntil.constant_until_forever(2), never_expiring.subtract(8, self.TOMORROW))

    def test_cannot_subtract_when_not_enough_miles(self):
        # given
        never_expiring: Miles = ConstantUntil.constant_until_forever(10)
        expiring_miles: Miles = ConstantUntil.constant_until(10, self.TODAY)

        # expect
        with self.assertRaises(AttributeError):
            never_expiring.subtract(11, self.YESTERDAY)
        with self.assertRaises(AttributeError):
            never_expiring.subtract(11, self.TODAY)
        with self.assertRaises(AttributeError):
            never_expiring.subtract(11, self.TOMORROW)

        with self.assertRaises(AttributeError):
            expiring_miles.subtract(11, self.YESTERDAY)
        with self.assertRaises(AttributeError):
            expiring_miles.subtract(11, self.TODAY)
        with self.assertRaises(AttributeError):
            expiring_miles.subtract(8, self.TOMORROW)

    def test_cannot_subtract_from_two_step_expiring_miles(self):
        # given
        expiring_in_two_steps_miles: Miles = TwoStepExpiringMiles(10, self.YESTERDAY, self.TODAY)

        with self.assertRaises(AttributeError):
            expiring_in_two_steps_miles.subtract(11, self.YESTERDAY)
        with self.assertRaises(AttributeError):
            expiring_in_two_steps_miles.subtract(11, self.TODAY)
        with self.assertRaises(AttributeError):
            expiring_in_two_steps_miles.subtract(11, self.TOMORROW)
        with self.assertRaises(AttributeError):
            expiring_in_two_steps_miles.subtract(2, self.TOMORROW)

    def test_can_subtract_from_two_step_expiring_miles(self):
        # given
        two_step_expiring = TwoStepExpiringMiles(10, self.YESTERDAY, self.TODAY)

        # expect
        self.assertEqual(10, two_step_expiring.get_amount_for(self.YESTERDAY))
        self.assertEqual(5, two_step_expiring.get_amount_for(self.TODAY))
        self.assertEqual(0, two_step_expiring.get_amount_for(self.TOMORROW))

    def test_can_subtract_from_two_step_expiring_miles_when_enough_miles(self):
        # given
        two_step_expiring_odd = TwoStepExpiringMiles(9, self.YESTERDAY, self.TODAY)
        two_step_expiring_even = TwoStepExpiringMiles(10, self.YESTERDAY, self.TODAY)

        # expect
        self.assertEqual(
            TwoStepExpiringMiles(4, self.YESTERDAY, self.TODAY),
            two_step_expiring_odd.subtract(5, self.YESTERDAY)
        )
        self.assertEqual(
            TwoStepExpiringMiles(1, self.YESTERDAY, self.TODAY),
            two_step_expiring_odd.subtract(4, self.TODAY)
        )

        self.assertEqual(
            TwoStepExpiringMiles(5, self.YESTERDAY, self.TODAY),
            two_step_expiring_even.subtract(5, self.YESTERDAY)
        )
        self.assertEqual(
            TwoStepExpiringMiles(0, self.YESTERDAY, self.TODAY),
            two_step_expiring_even.subtract(5, self.TODAY)
        )
