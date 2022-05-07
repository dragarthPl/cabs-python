from datetime import datetime
from typing import List
from unittest import TestCase

import pytz
from dateutil.relativedelta import relativedelta
from freezegun import freeze_time
from fastapi.params import Depends

from config.app_properties import AppProperties
from core.database import create_db_and_tables, drop_db_and_tables
from entity import Transit, Client, AwardedMiles
from money import Money
from repository.awarded_miles_repository import AwardedMilesRepositoryImp
from service.awards_service import AwardsService, AwardsServiceImpl

from tests.common.fixtures import DependencyResolver, Fixtures

dependency_resolver = DependencyResolver()

class TestRemovingAwardMilesIntegration(TestCase):
    DAY_BEFORE_YESTERDAY = datetime(1989, 12, 12, 12, 12).astimezone(pytz.utc)
    YESTERDAY = DAY_BEFORE_YESTERDAY + relativedelta(days=1)
    TODAY = YESTERDAY + relativedelta(days=1)
    SUNDAY = datetime(1989, 12, 17, 12, 12).astimezone(pytz.utc)

    awards_service: AwardsService = dependency_resolver.resolve_dependency(Depends(AwardsServiceImpl))
    awarded_miles_repository: AwardedMilesRepositoryImp = dependency_resolver.resolve_dependency(
        Depends(AwardedMilesRepositoryImp))
    fixtures: Fixtures = dependency_resolver.resolve_dependency(Depends(Fixtures))
    app_properties: AppProperties = dependency_resolver.resolve_dependency(Depends(AppProperties))

    def setUp(self):
        create_db_and_tables()

    def test_by_default_remove_oldest_first_even_when_they_are_non_expiring(self):
        # given
        client = self.client_with_an_active_miles_program(Client.Type.NORMAL)
        # and
        transit = self.fixtures.a_transit_price(Money(80))
        # and
        middle = self.granted_miles_that_will_expire_in_days(10, 365, self.YESTERDAY, client, transit)
        youngest = self.granted_miles_that_will_expire_in_days(10, 365, self.TODAY, client, transit)
        oldest_non_expiring_miles = self.granted_non_expiring_miles(5, self.DAY_BEFORE_YESTERDAY, client)

        # when
        with freeze_time(self.DAY_BEFORE_YESTERDAY):
            self.awards_service.remove_miles(client.id, 16)

        # then
        awarded_miles = self.awarded_miles_repository.find_all_by_client(client)
        self.assert_that_miles_were_reduced_to(oldest_non_expiring_miles, 0, awarded_miles)
        self.assert_that_miles_were_reduced_to(middle, 0, awarded_miles)
        self.assert_that_miles_were_reduced_to(youngest, 9, awarded_miles)

    def test_should_remove_oldest_miles_first_when_many_transits(self):
        # given
        client = self.client_with_an_active_miles_program(Client.Type.NORMAL)
        # and
        self.fixtures.client_has_done_transits(client, 15)
        # and
        transit = self.fixtures.a_transit_price(Money(100))
        # and
        oldest = self.granted_miles_that_will_expire_in_days(10, 60, self.DAY_BEFORE_YESTERDAY, client, transit)
        middle = self.granted_miles_that_will_expire_in_days(10, 365, self.YESTERDAY, client, transit)
        youngest = self.granted_miles_that_will_expire_in_days(10, 60, self.TODAY, client, transit)

        # when
        with freeze_time(self.TODAY):
            self.awards_service.remove_miles(client.id, 15)

        # then
        awarded_miles = self.awarded_miles_repository.find_all_by_client(client)
        self.assert_that_miles_were_reduced_to(oldest, 0, awarded_miles)
        self.assert_that_miles_were_reduced_to(middle, 5, awarded_miles)
        self.assert_that_miles_were_reduced_to(youngest, 10, awarded_miles)

    def test_should_remove_non_expiring_miles_last_when_many_transits(self):
        # given
        client = self.client_with_an_active_miles_program(Client.Type.NORMAL)
        # and
        self.fixtures.client_has_done_transits(client, 15)
        # and
        transit = self.fixtures.a_transit_price(Money(80))

        regular_miles: AwardedMiles = self.granted_miles_that_will_expire_in_days(10, 365, self.TODAY, client, transit)
        oldest_non_expiring_miles: AwardedMiles = self.granted_non_expiring_miles(5, self.DAY_BEFORE_YESTERDAY, client)

        # when
        with freeze_time(self.DAY_BEFORE_YESTERDAY):
            self.awards_service.remove_miles(client.id, 13)

        # then
        awarded_miles = self.awarded_miles_repository.find_all_by_client(client)
        self.assert_that_miles_were_reduced_to(regular_miles, 0, awarded_miles)
        self.assert_that_miles_were_reduced_to(oldest_non_expiring_miles, 2, awarded_miles)

    def test_should_remove_soon_to_expire_miles_first_when_client_is_vip(self):
        # given
        client = self.client_with_an_active_miles_program(Client.Type.VIP)
        # and
        transit = self.fixtures.a_transit_price(Money(80))
        # and

        second_to_expire: AwardedMiles = self.granted_miles_that_will_expire_in_days(
            10, 60, self.YESTERDAY, client, transit)
        third_to_expire: AwardedMiles = self.granted_miles_that_will_expire_in_days(
            5, 365, self.DAY_BEFORE_YESTERDAY, client, transit)
        first_to_expire: AwardedMiles = self.granted_miles_that_will_expire_in_days(
            15, 30, self.TODAY, client, transit)
        non_expiring: AwardedMiles = self.granted_non_expiring_miles(
            1, self.DAY_BEFORE_YESTERDAY, client)

        # when
        with freeze_time(self.DAY_BEFORE_YESTERDAY):
            self.awards_service.remove_miles(client.id, 21)

        # then
        awarded_miles = self.awarded_miles_repository.find_all_by_client(client)
        self.assert_that_miles_were_reduced_to(non_expiring, 1, awarded_miles)
        self.assert_that_miles_were_reduced_to(first_to_expire, 0, awarded_miles)
        self.assert_that_miles_were_reduced_to(second_to_expire, 4, awarded_miles)
        self.assert_that_miles_were_reduced_to(third_to_expire, 5, awarded_miles)

    def test_should_remove_soon_to_expire_miles_first_when_removing_on_sunday_and_client_has_done_many_transits(self):
        # given
        client = self.client_with_an_active_miles_program(Client.Type.NORMAL)
        # and
        self.fixtures.client_has_done_transits(client, 15)
        # and
        transit = self.fixtures.a_transit_price(Money(80))
        # and
        second_to_expire: AwardedMiles = self.granted_miles_that_will_expire_in_days(
            10, 60, self.YESTERDAY, client, transit)
        third_to_expire: AwardedMiles = self.granted_miles_that_will_expire_in_days(
            5, 365, self.DAY_BEFORE_YESTERDAY, client, transit)
        first_to_expire: AwardedMiles = self.granted_miles_that_will_expire_in_days(
            15, 10, self.TODAY, client, transit)
        non_expiring: AwardedMiles = self.granted_non_expiring_miles(
            100, self.YESTERDAY, client)

        # when
        with freeze_time(self.SUNDAY):
            self.awards_service.remove_miles(client.id, 21)

        # then
        awarded_miles = self.awarded_miles_repository.find_all_by_client(client)
        self.assert_that_miles_were_reduced_to(non_expiring, 100, awarded_miles)
        self.assert_that_miles_were_reduced_to(first_to_expire, 0, awarded_miles)
        self.assert_that_miles_were_reduced_to(second_to_expire, 4, awarded_miles)
        self.assert_that_miles_were_reduced_to(third_to_expire, 5, awarded_miles)

    def test_should_remove_expiring_miles_first_when_client_has_many_claims(self):
        # given
        client = self.client_with_an_active_miles_program(Client.Type.NORMAL)
        # and
        self.fixtures.client_has_done_claims(client, 3)
        # and
        transit = self.fixtures.a_transit_price(Money(80))
        # and
        second_to_expire: AwardedMiles = self.granted_miles_that_will_expire_in_days(
            4, 60, self.YESTERDAY, client, transit)
        third_to_expire: AwardedMiles = self.granted_miles_that_will_expire_in_days(
            10, 365, self.DAY_BEFORE_YESTERDAY, client, transit)
        first_to_expire: AwardedMiles = self.granted_miles_that_will_expire_in_days(
            5, 10, self.YESTERDAY, client, transit)
        non_expiring: AwardedMiles = self.granted_non_expiring_miles(
            10, self.YESTERDAY, client)

        # when
        with freeze_time(self.YESTERDAY):
            self.awards_service.remove_miles(client.id, 21)

        # then
        awarded_miles = self.awarded_miles_repository.find_all_by_client(client)
        self.assert_that_miles_were_reduced_to(non_expiring, 0, awarded_miles)
        self.assert_that_miles_were_reduced_to(third_to_expire, 0, awarded_miles)
        self.assert_that_miles_were_reduced_to(second_to_expire, 3, awarded_miles)
        self.assert_that_miles_were_reduced_to(first_to_expire, 5, awarded_miles)

    def granted_miles_that_will_expire_in_days(
            self,
            miles: int,
            expiration_in_days: int,
            when: datetime,
            client: Client,
            transit: Transit
    ) -> AwardedMiles:
        self.miles_will_expire_in_days(expiration_in_days)
        self.default_miles_bonus_is(miles)
        return self.miles_registered_at(when, client, transit)

    def granted_non_expiring_miles(self, miles: int, when: datetime, client: Client) -> AwardedMiles:
        self.default_miles_bonus_is(miles)
        with freeze_time(when):
            return self.awards_service.register_non_expiring_miles(client.id, miles)

    def assert_that_miles_were_reduced_to(
            self,
            first_to_expire: AwardedMiles,
            miles_after_reduction: int,
            all_miles: List[AwardedMiles]
    ):
        actual = list(
            map(
                lambda am: am.miles,
                filter(lambda am: first_to_expire.id == am.id, all_miles)
            )
        )
        self.assertEqual(miles_after_reduction, actual[0])

    def miles_registered_at(self, when: datetime, client: Client, transit: Transit) -> AwardedMiles:
        with freeze_time(when):
            return self.awards_service.register_miles(client.id, transit.id)

    def client_with_an_active_miles_program(self, client_type: Client.Type) -> Client:
        with freeze_time(self.DAY_BEFORE_YESTERDAY):
            client = self.fixtures.a_client_with_type(client_type)
            self.fixtures.active_awards_account(client)
            return client

    def miles_will_expire_in_days(self, days: int):
        self.awards_service.app_properties.miles_expiration_in_days = days

    def tearDown(self) -> None:
        drop_db_and_tables()

    def default_miles_bonus_is(self, miles: int):
        self.awards_service.app_properties.default_miles_bonus = miles
