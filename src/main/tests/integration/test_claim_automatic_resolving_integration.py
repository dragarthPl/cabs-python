from datetime import datetime
from unittest import TestCase

from fastapi.params import Depends
from mockito import when, verify, mock, ANY, verifyZeroInteractions

from config.app_properties import AppProperties
from core.database import create_db_and_tables, drop_db_and_tables
from entity import Client, Driver, Transit, Claim
from service.awards_service import AwardsService, AwardsServiceImpl
from service.claim_service import ClaimService
from service.client_notification_service import ClientNotificationService
from service.driver_notification_service import DriverNotificationService
from tests.common.fixtures import DependencyResolver, Fixtures

dependency_resolver = DependencyResolver()

class TestClaimAutomaticResolvingIntegration(TestCase):
    claim_service: ClaimService = dependency_resolver.resolve_dependency(Depends(ClaimService))

    client_notification_service: ClientNotificationService = dependency_resolver.resolve_dependency(
        Depends(ClientNotificationService))

    driver_notification_service: DriverNotificationService = dependency_resolver.resolve_dependency(
        Depends(DriverNotificationService))

    awards_service: AwardsServiceImpl = dependency_resolver.resolve_dependency(Depends(AwardsServiceImpl))

    app_properties: AppProperties = dependency_resolver.resolve_dependency(Depends(AppProperties))

    fixtures: Fixtures = dependency_resolver.resolve_dependency(Depends(Fixtures))

    def setUp(self):
        create_db_and_tables()

    def test_second_claim_for_the_same_transit_will_be_escalated(self):
        # given
        self.low_cost_threshold_is(40)
        # and
        driver: Driver = self.fixtures.a_driver()
        # and
        client: Client = self.fixtures.a_client_with_type(Client.Type.VIP)
        # and
        transit: Transit = self.a_transit(client, driver, 39)
        # and

        claim: Claim = self.fixtures.create_claim(client, transit)
        # and
        claim = self.claim_service.try_to_automatically_resolve(claim.id)
        # and
        claim2: Claim = self.fixtures.create_claim(client, transit)

        # when
        claim2 = self.claim_service.try_to_automatically_resolve(claim2.id)

        # then
        self.assertEquals(Claim.Status.REFUNDED, claim.status)
        self.assertEquals(Claim.CompletionMode.AUTOMATIC, claim.completion_mode)
        self.assertEquals(Claim.Status.ESCALATED, claim2.status)
        self.assertEquals(Claim.CompletionMode.MANUAL, claim2.completion_mode)

    def test_low_cost_transits_are_refunded_if_client_is_vip(self):
        # given
        self.low_cost_threshold_is(40)
        # and
        client: Client = self.fixtures.a_client_with_claims(Client.Type.VIP, 3)
        # and
        driver = self.fixtures.a_driver()
        # and
        transit: Transit = self.a_transit(client, driver, 39)
        # and
        claim: Claim = self.fixtures.create_claim(client, transit)

        # when
        self.claim_service.awards_service = mock()
        self.claim_service.client_notification_service = mock()
        claim = self.claim_service.try_to_automatically_resolve(claim.id)

        # then
        self.assertEquals(Claim.Status.REFUNDED, claim.status)
        self.assertEquals(Claim.CompletionMode.AUTOMATIC, claim.completion_mode)
        verify(self.claim_service.client_notification_service).notify_client_about_refund(claim.claim_no,
                                                                                          claim.owner.id)
        verify(self.claim_service.awards_service).register_non_expiring_miles(claim.owner.id, 10)

    def test_high_cost_transits_are_escalated_even_when_client_is_vip(self):
        # given
        self.low_cost_threshold_is(40)
        # and
        client: Client = self.fixtures.a_client_with_claims(Client.Type.VIP, 3)
        # and
        driver = self.fixtures.a_driver()
        # and
        transit: Transit = self.a_transit(client, driver, 50)
        # and
        claim: Claim = self.fixtures.create_claim(client, transit)

        # when
        self.claim_service.awards_service = mock()
        self.claim_service.driver_notification_service = mock()
        claim = self.claim_service.try_to_automatically_resolve(claim.id)

        # then
        self.assertEquals(Claim.Status.ESCALATED, claim.status)
        self.assertEquals(Claim.CompletionMode.MANUAL, claim.completion_mode)
        verify(
            self.claim_service.driver_notification_service
        ).ask_driver_for_details_about_claim(claim.claim_no, driver.id)
        verifyZeroInteractions(self.claim_service.awards_service)

    def test_first_three_claims_are_refunded(self):
        # given
        self.low_cost_threshold_is(40)
        # and
        self.no_of_transits_for_automatic_refund_is(10)
        # and
        client: Client = self.a_client(Client.Type.NORMAL)
        # and
        driver = self.fixtures.a_driver()

        # when
        self.claim_service.awards_service = mock()
        self.claim_service.client_notification_service = mock()
        claim1: Claim = self.claim_service.try_to_automatically_resolve(
            self.fixtures.create_claim(client, self.a_transit(client, driver, 50)).id)

        claim2: Claim = self.claim_service.try_to_automatically_resolve(
            self.fixtures.create_claim(client, self.a_transit(client, driver, 50)).id)

        claim3: Claim = self.claim_service.try_to_automatically_resolve(
            self.fixtures.create_claim(client, self.a_transit(client, driver, 50)).id)

        claim4: Claim = self.claim_service.try_to_automatically_resolve(
            self.fixtures.create_claim(client, self.a_transit(client, driver, 50)).id)

        # then
        self.assertEqual(Claim.Status.REFUNDED, claim1.status)
        self.assertEqual(Claim.Status.REFUNDED, claim2.status)
        self.assertEqual(Claim.Status.REFUNDED, claim3.status)
        self.assertEqual(Claim.Status.ESCALATED, claim4.status)
        self.assertEqual(Claim.CompletionMode.AUTOMATIC, claim1.completion_mode)
        self.assertEqual(Claim.CompletionMode.AUTOMATIC, claim2.completion_mode)
        self.assertEqual(Claim.CompletionMode.AUTOMATIC, claim3.completion_mode)
        self.assertEqual(Claim.CompletionMode.MANUAL, claim4.completion_mode)

        verify(
            self.claim_service.client_notification_service,
            times=3,
        ).notify_client_about_refund(claim1.claim_no, client.id)
        verify(
            self.claim_service.client_notification_service,
            times=3,
        ).notify_client_about_refund(claim2.claim_no, client.id)
        verify(
            self.claim_service.client_notification_service,
            times=3,
        ).notify_client_about_refund(claim3.claim_no, client.id)
        verifyZeroInteractions(self.claim_service.awards_service)

    def test_low_cost_transits_are_refunded_when_many_transits(self):
        # given
        self.low_cost_threshold_is(40)
        # and
        self.no_of_transits_for_automatic_refund_is(10)
        # and
        client: Client = self.fixtures.a_client_with_claims(Client.Type.NORMAL, 3)
        # and
        self.fixtures.client_has_done_transits(client, 12)
        # and
        transit: Transit = self.a_transit(client, self.fixtures.a_driver(), 39)
        # and
        claim = self.fixtures.create_claim(client, transit)

        # when
        self.claim_service.awards_service = mock()
        self.claim_service.client_notification_service = mock()
        claim = self.claim_service.try_to_automatically_resolve(claim.id)

        self.assertEqual(Claim.Status.REFUNDED, claim.status)
        self.assertEqual(Claim.CompletionMode.AUTOMATIC, claim.completion_mode)
        verify(
            self.claim_service.client_notification_service,
        ).notify_client_about_refund(claim.claim_no, client.id)
        verifyZeroInteractions(self.claim_service.awards_service)

    def test_high_cost_transits_are_escalated_even_with_many_transits(self):
        # given
        self.low_cost_threshold_is(40)
        # and
        self.no_of_transits_for_automatic_refund_is(10)
        # and
        client: Client = self.fixtures.a_client_with_claims(Client.Type.NORMAL, 3)
        # and
        self.fixtures.client_has_done_transits(client, 12)
        # and
        transit: Transit = self.a_transit(client, self.fixtures.a_driver(), 50)
        # and
        claim = self.fixtures.create_claim(client, transit)

        # when
        self.claim_service.awards_service = mock()
        self.claim_service.client_notification_service = mock()
        claim = self.claim_service.try_to_automatically_resolve(claim.id)

        self.assertEqual(Claim.Status.ESCALATED, claim.status)
        self.assertEqual(Claim.CompletionMode.MANUAL, claim.completion_mode)
        verify(
            self.claim_service.client_notification_service,
        ).ask_for_more_information(claim.claim_no, client.id)
        verifyZeroInteractions(self.claim_service.awards_service)

    def test_high_cost_transits_are_escalated_when_few_transits(self):
        # given
        self.low_cost_threshold_is(40)
        # and
        self.no_of_transits_for_automatic_refund_is(10)
        # and
        client: Client = self.fixtures.a_client_with_claims(Client.Type.NORMAL, 3)
        # and
        self.fixtures.client_has_done_transits(client, 2)
        # and
        driver: Driver = self.fixtures.a_driver()
        # and
        claim = self.fixtures.create_claim(client, self.a_transit(client, driver, 50))

        # when
        self.claim_service.awards_service = mock()
        self.claim_service.driver_notification_service = mock()
        claim = self.claim_service.try_to_automatically_resolve(claim.id)

        # then
        self.assertEqual(Claim.Status.ESCALATED, claim.status)
        self.assertEqual(Claim.CompletionMode.MANUAL, claim.completion_mode)
        verify(
            self.claim_service.driver_notification_service,
        ).ask_driver_for_details_about_claim(claim.claim_no, driver.id)
        verifyZeroInteractions(self.claim_service.awards_service)

    def a_transit(self, client: Client, driver: Driver, price: int) -> Transit:
        return self.fixtures._a_completed_transit_at(price, datetime.now(), client, driver)

    def low_cost_threshold_is(self, price: int) -> None:
        self.claim_service.app_properties.automatic_refund_for_vip_threshold = price

    def no_of_transits_for_automatic_refund_is(self, no: int) -> None:
        self.claim_service.app_properties.no_of_transits_for_claim_automatic_refund = no

    def a_client(self, client_type: Client.Type) -> Client:
        return self.fixtures.a_client_with_claims(client_type, 0)

    def tearDown(self) -> None:
        drop_db_and_tables()
