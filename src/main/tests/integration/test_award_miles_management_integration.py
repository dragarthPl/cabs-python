from datetime import datetime
from unittest import TestCase

import pytz
from mockito import when

from core.database import create_db_and_tables, drop_db_and_tables
from loyalty.awards_account_repository import AwardsAccountRepositoryImp
from loyalty.awards_service import AwardsService
from ride.transit import Transit

from tests.common.fixtures import DependencyResolver, Fixtures

dependency_resolver = DependencyResolver()

class TestAwardMilesManagementIntegration(TestCase):
    TRANSIT_ID: int = 1
    NOW = datetime(1989, 12, 12, 12, 12).astimezone(pytz.utc)

    awards_service: AwardsService = dependency_resolver.resolve_dependency(AwardsService)
    awards_account_repository: AwardsAccountRepositoryImp = dependency_resolver.resolve_dependency(
        AwardsAccountRepositoryImp)
    fixtures: Fixtures = dependency_resolver.resolve_dependency(Fixtures)

    def setUp(self):
        create_db_and_tables()
        when(self.awards_service.transit_repository).get_one(self.TRANSIT_ID).thenReturn(Transit())

    def test_can_register_account(self):
        # given
        client = self.fixtures.a_client()

        # when
        self.awards_service.register_to_program(client.id)

        # then
        account = self.awards_service.find_by(client.id)
        self.assertIsNotNone(account)
        self.assertEqual(client.id, account.client.id)
        self.assertFalse(account.is_active)
        self.assertEqual(0, account.transactions)

    def test_can_activate_account(self):
        # given
        client = self.fixtures.a_client()
        # and
        self.awards_service.register_to_program(client.id)

        # when
        self.awards_service.activate_account(client.id)

        # then
        account = self.awards_service.find_by(client.id)
        self.assertTrue(account.is_active)

    def test_can_deactivate_account(self):
        # given
        client = self.fixtures.a_client()
        # and
        self.fixtures.active_awards_account(client)

        # when
        self.awards_service.deactivate_account(client.id)

        # then
        account = self.awards_service.find_by(client.id)
        self.assertFalse(account.is_active)

    def test_can_register_miles(self):
        # given
        client = self.fixtures.a_client()
        # and
        self.fixtures.active_awards_account(client)

        # when
        self.awards_service.register_miles(client.id, self.TRANSIT_ID)

        # then
        account = self.awards_service.find_by(client.id)
        self.assertEqual(1, account.transactions)
        awarded_miles = self.awards_account_repository.find_all_miles_by(client)
        self.assertEqual(1, len(awarded_miles))
        self.assertEqual(10, awarded_miles[0].get_miles_amount(self.NOW))
        self.assertFalse(awarded_miles[0].can_expire())

    def test_can_register_non_expiring_miles(self):
        # given
        client = self.fixtures.a_client()
        # and
        self.fixtures.active_awards_account(client)

        # when
        self.awards_service.register_non_expiring_miles(client.id, 20)

        # then
        account = self.awards_service.find_by(client.id)
        self.assertEqual(1, account.transactions)
        awarded_miles = self.awards_account_repository.find_all_miles_by(client)
        self.assertEqual(1, len(awarded_miles))
        self.assertEqual(20, awarded_miles[0].get_miles_amount(self.NOW))
        self.assertTrue(awarded_miles[0].can_expire())

    def test_can_calculate_miles_balance(self):
        # given
        client = self.fixtures.a_client()
        # and
        self.fixtures.active_awards_account(client)

        # when
        self.awards_service.register_non_expiring_miles(client.id, 20)
        self.awards_service.register_miles(client.id, self.TRANSIT_ID)
        self.awards_service.register_miles(client.id, self.TRANSIT_ID)

        # then
        account = self.awards_service.find_by(client.id)
        self.assertEqual(3, account.transactions)
        miles = self.awards_service.calculate_balance(client.id)
        self.assertEqual(40, miles)

    def test_can_transfer_miles(self):
        # given
        client = self.fixtures.a_client()
        second_client = self.fixtures.a_client()
        # and
        self.fixtures.active_awards_account(client)
        self.fixtures.active_awards_account(second_client)
        # and
        self.awards_service.register_non_expiring_miles(client.id, 10)

        # when
        self.awards_service.transfer_miles(client.id, second_client.id, 10)

        # then
        first_client_balance = self.awards_service.calculate_balance(client.id)
        second_client_balance = self.awards_service.calculate_balance(second_client.id)
        self.assertEqual(0, first_client_balance)
        self.assertEqual(10, second_client_balance)

    def test_cannot_transfer_miles_when_account_is_not_active(self):
        # given
        client = self.fixtures.a_client()
        second_client = self.fixtures.a_client()
        # and
        self.fixtures.active_awards_account(client)
        self.fixtures.active_awards_account(second_client)
        # and
        self.awards_service.register_non_expiring_miles(client.id, 10)
        # and
        self.awards_service.deactivate_account(client.id)

        # when
        self.awards_service.transfer_miles(client.id, second_client.id, 10)

        # then
        self.assertEqual(10, self.awards_service.calculate_balance(client.id))

    def test_cannot_transfer_miles_when_not_enough(self):
        # given
        client = self.fixtures.a_client()
        second_client = self.fixtures.a_client()
        # and
        self.fixtures.active_awards_account(client)
        self.fixtures.active_awards_account(second_client)
        # and
        self.awards_service.register_non_expiring_miles(client.id, 10)

        # when
        self.awards_service.transfer_miles(client.id, second_client.id, 30)

        # then
        self.assertEqual(10, self.awards_service.calculate_balance(client.id))

    def test_cannot_transfer_miles_when_account_not_active(self):
        # given
        client = self.fixtures.a_client()
        second_client = self.fixtures.a_client()
        # and
        self.fixtures.active_awards_account(client)
        self.fixtures.active_awards_account(second_client)
        # and
        self.awards_service.register_non_expiring_miles(client.id, 10)
        # and
        self.awards_service.deactivate_account(client.id)

        # when
        self.awards_service.transfer_miles(client.id, second_client.id, 10)
        # then
        self.assertEqual(10, self.awards_service.calculate_balance(client.id))

    def test_can_remove_miles(self):
        # given
        client = self.fixtures.a_client()
        # and
        self.fixtures.active_awards_account(client)
        # and
        self.awards_service.register_miles(client.id, self.TRANSIT_ID)
        self.awards_service.register_miles(client.id, self.TRANSIT_ID)
        self.awards_service.register_miles(client.id, self.TRANSIT_ID)

        # when
        self.awards_service.remove_miles(client.id, 20)

        # then
        miles = self.awards_service.calculate_balance(client.id)
        self.assertEqual(10, miles)

    def test_cannot_remove_more_than_client_has_miles(self):
        # given
        client = self.fixtures.a_client()
        # and
        self.fixtures.active_awards_account(client)

        # when
        self.awards_service.register_miles(client.id, self.TRANSIT_ID)
        self.awards_service.register_miles(client.id, self.TRANSIT_ID)
        self.awards_service.register_miles(client.id, self.TRANSIT_ID)

        # then
        with self.assertRaises(AttributeError):
            self.awards_service.remove_miles(client.id, 40)

    def test_cannot_remove_miles_if_account_is_not_active(self):
        # given
        client = self.fixtures.a_client()
        # and
        self.awards_service.register_to_program(client.id)
        # and
        current_miles = self.awards_service.calculate_balance(client.id)

        # when
        self.awards_service.register_miles(client.id, self.TRANSIT_ID)

        # then
        self.assertEqual(current_miles, self.awards_service.calculate_balance(client.id))

    def tearDown(self) -> None:
        drop_db_and_tables()
