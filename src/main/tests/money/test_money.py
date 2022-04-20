from unittest import TestCase

from money import Money


class TestMoney(TestCase):

    def test_can_create_money_from_integer(self):
        # expect
        self.assertEqual("100.00", Money(10000).to_string())
        self.assertEqual("0.00", Money(0).to_string())
        self.assertEqual("10.12", Money(1012).to_string())

    def test_should_project_money_to_integer(self):
        # expect
        self.assertEqual(10, Money(10).to_int())
        self.assertEqual(0, Money(0).to_int())
        self.assertEqual(-5, Money(-5).to_int())

    def test_can_add_money(self):
        # expect
        self.assertEqual(Money(1000), Money(500).add(Money(500)))
        self.assertEqual(Money(1042), Money(1020).add(Money(22)))
        self.assertEqual(Money(0), Money(0).add(Money(0)))
        self.assertEqual(Money(-2), Money(-4).add(Money(2)))

    def test_can_subtract_money(self):
        # expect
        self.assertEqual(Money.ZERO, Money(50).subtract(Money(50)))
        self.assertEqual(Money(998), Money(1020).subtract(Money(22)))
        self.assertEqual(Money(-1), Money(2).subtract(Money(3)))

    def test_can_calculate_percentage(self):
        # expect
        self.assertEqual("30.00", Money(10000).percentage(30).to_string())
        self.assertEqual("26.40", Money(8800).percentage(30).to_string())
        self.assertEqual("88.00", Money(8800).percentage(100).to_string())
        self.assertEqual("0.00", Money(8800).percentage(0).to_string())
        self.assertEqual("13.20", Money(4400).percentage(30).to_string())
        self.assertEqual("0.30", Money(100).percentage(30).to_string())
        self.assertEqual("0.00", Money(1).percentage(40).to_string())
