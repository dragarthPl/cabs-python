from datetime import datetime
from unittest import TestCase

import pytz
from dateutil.relativedelta import relativedelta
from freezegun import freeze_time
from fastapi.params import Depends
from mockito import when

from config.app_properties import AppProperties
from core.database import create_db_and_tables, drop_db_and_tables
from entity import Transit, Client
from service.awards_service import AwardsService
from service.awards_service_impl import AwardsServiceImpl

from tests.common.fixtures import DependencyResolver, Fixtures

dependency_resolver = DependencyResolver()

class TestExpiringMilesIntegration(TestCase):
    TRANSIT_ID: int = 1
    _1989_12_12 = datetime(1989, 12, 12, 12, 12).astimezone(pytz.utc)
    _1989_12_13 = datetime(1989, 12, 13, 12, 12).astimezone(pytz.utc)
    _1989_12_14 = datetime(1989, 12, 14, 12, 12).astimezone(pytz.utc)

    awards_service: AwardsService = dependency_resolver.resolve_dependency(AwardsServiceImpl)
    fixtures: Fixtures = dependency_resolver.resolve_dependency(Fixtures)
    app_properties: AppProperties = dependency_resolver.resolve_dependency(AppProperties)

    def setUp(self):
        create_db_and_tables()
        when(self.awards_service.transit_repository).get_one(self.TRANSIT_ID).thenReturn(Transit())

    @freeze_time(_1989_12_12)
    def test_should_take_into_account_expired_miles_when_calculating_balance(self):
        # given
        client = self.fixtures.a_client()
        # and
        self.default_miles_bonus_is(10)
        # and
        self.default_miles_expiration_in_days_is(365)
        # and
        self.fixtures.active_awards_account(client)

        # when
        self.register_miles_at(client, self._1989_12_12)
        # then
        self.assertEqual(10, self.calculate_balance_at(client, self._1989_12_12))
        # when
        self.register_miles_at(client, self._1989_12_13)
        # then
        self.assertEqual(20, self.calculate_balance_at(client, self._1989_12_12))
        # when
        self.register_miles_at(client, self._1989_12_14)
        # then
        self.assertEqual(30, self.calculate_balance_at(client, self._1989_12_14))
        self.assertEqual(30, self.calculate_balance_at(client, self._1989_12_12 + relativedelta(days=300)))
        self.assertEqual(20, self.calculate_balance_at(client, self._1989_12_12 + relativedelta(days=365)))
        self.assertEqual(10, self.calculate_balance_at(client, self._1989_12_13 + relativedelta(days=365)))
        self.assertEqual(0, self.calculate_balance_at(client, self._1989_12_14 + relativedelta(days=365)))

    def default_miles_bonus_is(self, bonus: int) -> None:
        self.app_properties.default_miles_bonus = bonus

    def default_miles_expiration_in_days_is(self, days: int) -> None:
        self.app_properties.miles_expiration_in_days = days

    def register_miles_at(self, client: Client, when: datetime) -> None:
        with freeze_time(when):
            self.awards_service.register_miles(client.id, self.TRANSIT_ID)

    def calculate_balance_at(self, client: Client, when: datetime):
        with freeze_time(when):
            return self.awards_service.calculate_balance(client.id)

    def tearDown(self) -> None:
        drop_db_and_tables()
