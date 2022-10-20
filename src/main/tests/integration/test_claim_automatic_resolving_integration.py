from unittest import TestCase

from fastapi.params import Depends
from fastapi_events import middleware_identifier
from mockito import verify, mock, verifyZeroInteractions

from cabs_application import CabsApplication
from config.app_properties import AppProperties
from core.database import create_db_and_tables, drop_db_and_tables
from crm.claims.status import Status
from entity import Client, Driver, Transit, Claim, Address
from service.awards_service_impl import AwardsServiceImpl
from crm.claims.claim_service import ClaimService
from service.client_notification_service import ClientNotificationService
from service.driver_notification_service import DriverNotificationService
from service.geocoding_service import GeocodingService
from tests.common.fixtures import DependencyResolver, Fixtures

dependency_resolver = DependencyResolver()

class TestClaimAutomaticResolvingIntegration(TestCase):
    claim_service: ClaimService = dependency_resolver.resolve_dependency(ClaimService)

    client_notification_service: ClientNotificationService = dependency_resolver.resolve_dependency(
        ClientNotificationService)

    driver_notification_service: DriverNotificationService = dependency_resolver.resolve_dependency(
        DriverNotificationService)

    awards_service: AwardsServiceImpl = dependency_resolver.resolve_dependency(AwardsServiceImpl)

    app_properties: AppProperties = dependency_resolver.resolve_dependency(AppProperties)

    fixtures: Fixtures = dependency_resolver.resolve_dependency(Fixtures)

    geocoding_service: GeocodingService = dependency_resolver.resolve_dependency(GeocodingService)

    async def setUp(self):
        create_db_and_tables()
        app = CabsApplication().create_app()
        middleware_identifier.set(app.middleware_stack.app._id)

    async def test_second_claim_for_the_same_transit_will_be_escalated(self):
        # given
        self.low_cost_threshold_is(40)
        # and
        pickup: Address = self.fixtures.an_address()
        # and
        driver: Driver = self.fixtures.a_random_nearby_driver(self.geocoding_service, pickup)
        # and
        client: Client = self.fixtures.a_client_with_type(Client.Type.VIP)
        # and
        transit: Transit = self.a_transit(pickup, client, driver, 39)
        # and

        claim: Claim = self.fixtures.create_claim(client, transit)
        # and
        claim = self.claim_service.try_to_automatically_resolve(claim.id)
        # and
        claim2: Claim = self.fixtures.create_claim(client, transit)

        # when
        claim2 = self.claim_service.try_to_automatically_resolve(claim2.id)

        # then
        self.assertEquals(Status.REFUNDED, claim.status)
        self.assertEquals(Claim.CompletionMode.AUTOMATIC, claim.completion_mode)
        self.assertEquals(Status.ESCALATED, claim2.status)
        self.assertEquals(Claim.CompletionMode.MANUAL, claim2.completion_mode)

    async def test_low_cost_transits_are_refunded_if_client_is_vip(self):
        # given
        self.low_cost_threshold_is(40)
        # and
        client: Client = self.fixtures.a_client_with_claims(Client.Type.VIP, 3)
        # and
        pickup: Address = self.fixtures.an_address()
        # and
        driver: Driver = self.fixtures.a_random_nearby_driver(self.geocoding_service, pickup)
        # and
        transit: Transit = self.a_transit(pickup, client, driver, 39)
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
                                                                                          claim.owner_id)
        verify(self.claim_service.awards_service).register_non_expiring_miles(claim.owner_id, 10)

    async def test_high_cost_transits_are_escalated_even_when_client_is_vip(self):
        # given
        self.low_cost_threshold_is(40)
        # and
        client: Client = self.fixtures.a_client_with_claims(Client.Type.VIP, 3)
        # and
        pickup: Address = self.fixtures.an_address()
        # and
        driver: Driver = self.fixtures.a_random_nearby_driver(self.geocoding_service, pickup)
        # and
        transit: Transit = self.a_transit(pickup, client, driver, 50)
        # and
        claim: Claim = self.fixtures.create_claim(client, transit)

        # when
        self.claim_service.awards_service = mock()
        self.claim_service.driver_notification_service = mock()
        claim = self.claim_service.try_to_automatically_resolve(claim.id)

        # then
        self.assertEquals(Status.ESCALATED, claim.status)
        self.assertEquals(Claim.CompletionMode.MANUAL, claim.completion_mode)
        verify(
            self.claim_service.driver_notification_service
        ).ask_driver_for_details_about_claim(claim.claim_no, driver.id)
        verifyZeroInteractions(self.claim_service.awards_service)

    async def test_first_three_claims_are_refunded(self):
        # given
        self.low_cost_threshold_is(40)
        # and
        self.no_of_transits_for_automatic_refund_is(10)
        # and
        client: Client = self.a_client(Client.Type.NORMAL)
        # and
        pickup: Address = self.fixtures.an_address()
        # and
        driver: Driver = self.fixtures.a_random_nearby_driver(self.geocoding_service, pickup)

        # when
        self.claim_service.awards_service = mock()
        self.claim_service.client_notification_service = mock()
        claim1: Claim = self.claim_service.try_to_automatically_resolve(
            self.fixtures.create_claim(client, self.a_transit(pickup, client, driver, 50)).id)

        claim2: Claim = self.claim_service.try_to_automatically_resolve(
            self.fixtures.create_claim(client, self.a_transit(pickup, client, driver, 50)).id)

        claim3: Claim = self.claim_service.try_to_automatically_resolve(
            self.fixtures.create_claim(client, self.a_transit(pickup, client, driver, 50)).id)

        claim4: Claim = self.claim_service.try_to_automatically_resolve(
            self.fixtures.create_claim(client, self.a_transit(pickup, client, driver, 50)).id)

        # then
        self.assertEqual(Status.REFUNDED, claim1.status)
        self.assertEqual(Status.REFUNDED, claim2.status)
        self.assertEqual(Status.REFUNDED, claim3.status)
        self.assertEqual(Status.ESCALATED, claim4.status)
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

    async def test_low_cost_transits_are_refunded_when_many_transits(self):
        # given
        self.low_cost_threshold_is(40)
        # and
        self.no_of_transits_for_automatic_refund_is(10)
        # and
        client: Client = self.fixtures.a_client_with_claims(Client.Type.NORMAL, 3)
        # and
        self.fixtures.client_has_done_transits(client, 12, self.geocoding_service)
        # and
        pickup: Address = self.fixtures.an_address()
        # and
        driver: Driver = self.fixtures.a_random_nearby_driver(self.geocoding_service, pickup)
        # and
        transit: Transit = self.a_transit(pickup, client, driver, 39)
        # and
        claim = self.fixtures.create_claim(client, transit)

        # when
        self.claim_service.awards_service = mock()
        self.claim_service.client_notification_service = mock()
        claim = self.claim_service.try_to_automatically_resolve(claim.id)

        self.assertEqual(Status.REFUNDED, claim.status)
        self.assertEqual(Claim.CompletionMode.AUTOMATIC, claim.completion_mode)
        verify(
            self.claim_service.client_notification_service,
        ).notify_client_about_refund(claim.claim_no, client.id)
        verifyZeroInteractions(self.claim_service.awards_service)

    async def test_high_cost_transits_are_escalated_even_with_many_transits(self):
        # given
        self.low_cost_threshold_is(40)
        # and
        self.no_of_transits_for_automatic_refund_is(10)
        # and
        client: Client = self.fixtures.a_client_with_claims(Client.Type.NORMAL, 3)
        # and
        self.fixtures.client_has_done_transits(client, 12, self.geocoding_service)
        # and
        pickup: Address = self.fixtures.an_address()
        # and
        driver: Driver = self.fixtures.a_random_nearby_driver(self.geocoding_service, pickup)
        # and
        transit: Transit = self.a_transit(pickup, client, driver, 50)
        # and
        claim = self.fixtures.create_claim(client, transit)

        # when
        self.claim_service.awards_service = mock()
        self.claim_service.client_notification_service = mock()
        claim = self.claim_service.try_to_automatically_resolve(claim.id)

        self.assertEqual(Status.ESCALATED, claim.status)
        self.assertEqual(Claim.CompletionMode.MANUAL, claim.completion_mode)
        verify(
            self.claim_service.client_notification_service,
        ).ask_for_more_information(claim.claim_no, client.id)
        verifyZeroInteractions(self.claim_service.awards_service)

    async def test_high_cost_transits_are_escalated_when_few_transits(self):
        # given
        self.low_cost_threshold_is(40)
        # and
        self.no_of_transits_for_automatic_refund_is(10)
        # and
        client: Client = self.fixtures.a_client_with_claims(Client.Type.NORMAL, 3)
        # and
        self.fixtures.client_has_done_transits(client, 2, self.geocoding_service)
        # and
        pickup: Address = self.fixtures.an_address()
        # and
        driver: Driver = self.fixtures.a_random_nearby_driver(self.geocoding_service, pickup)
        # and
        claim = self.fixtures.create_claim(client, self.a_transit(pickup, client, driver, 50))

        # when
        self.claim_service.awards_service = mock()
        self.claim_service.driver_notification_service = mock()
        claim = self.claim_service.try_to_automatically_resolve(claim.id)

        # then
        self.assertEqual(Status.ESCALATED, claim.status)
        self.assertEqual(Claim.CompletionMode.MANUAL, claim.completion_mode)
        verify(
            self.claim_service.driver_notification_service,
        ).ask_driver_for_details_about_claim(claim.claim_no, driver.id)
        verifyZeroInteractions(self.claim_service.awards_service)

    async def a_transit(self, pickup: Address, client: Client, driver: Driver, price: int) -> Transit:
        return self.fixtures.a_journey(price, client, driver, pickup, self.fixtures.an_address())

    async def low_cost_threshold_is(self, price: int) -> None:
        self.claim_service.app_properties.automatic_refund_for_vip_threshold = price

    async def no_of_transits_for_automatic_refund_is(self, no: int) -> None:
        self.claim_service.app_properties.no_of_transits_for_claim_automatic_refund = no

    async def a_client(self, client_type: Client.Type) -> Client:
        return self.fixtures.a_client_with_claims(client_type, 0)

    async def tearDown(self) -> None:
        drop_db_and_tables()
