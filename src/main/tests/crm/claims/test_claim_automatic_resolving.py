from unittest import TestCase

from crm.claims.claim import Claim
from crm.claims.claims_resolver import ClaimsResolver
from crm.claims.status import Status
from crm.client import Client
from money import Money
from ride.transit import Transit


class TestClaimAutomaticResolving(TestCase):
    def test_second_claim_for_the_same_transit_will_be_escalated(self):
        # given
        resolver = ClaimsResolver()
        # and
        transit = self.a_transit(1)
        # and
        claim: Claim = self.create_claim(transit, 39)
        # and
        resolver.resolve(claim, Client.Type.NORMAL, 40, 15, 10)
        # and
        claim2: Claim = self.create_claim(transit, 39)

        # when
        result: ClaimsResolver.Result = resolver.resolve(claim2, Client.Type.NORMAL, 40, 15, 10)

        # then
        self.assertEqual(Status.ESCALATED, result.decision)
        self.assertEqual(ClaimsResolver.WhoToAsk.ASK_NOONE, result.who_to_ask)

    def test_low_cost_transits_are_refunded_if_client_is_vip(self):
        # given
        resolver = ClaimsResolver()
        # and
        transit = self.a_transit(1)
        # and
        claim: Claim = self.create_claim(transit, 39)

        # when
        result: ClaimsResolver.Result = resolver.resolve(claim, Client.Type.VIP, 40, 15, 10)

        # then
        self.assertEqual(Status.REFUNDED, result.decision)
        self.assertEqual(ClaimsResolver.WhoToAsk.ASK_NOONE, result.who_to_ask)

    def test_high_cost_transits_are_escalated_even_when_client_is_vip(self):
        # given
        resolver = ClaimsResolver()
        # and
        claim = self.create_claim(self.a_transit(1), 39)
        resolver.resolve(claim, Client.Type.VIP, 40, 15, 10)
        claim2 = self.create_claim(self.a_transit(2), 39)
        resolver.resolve(claim2, Client.Type.VIP, 40, 15, 10)
        claim3 = self.create_claim(self.a_transit(3), 39)
        resolver.resolve(claim3, Client.Type.VIP, 40, 15, 10)
        # and
        claim4 = self.create_claim(self.a_transit(4), 41)

        # when
        result: ClaimsResolver.Result = resolver.resolve(claim4, Client.Type.VIP, 40, 15, 10)

        # then
        self.assertEqual(Status.ESCALATED, result.decision)
        self.assertEqual(ClaimsResolver.WhoToAsk.ASK_DRIVER, result.who_to_ask)

    def test_first_three_claims_are_refunded(self):
        # given
        resolver = ClaimsResolver()
        # and
        claim = self.create_claim(self.a_transit(1), 39)
        result1 = resolver.resolve(claim, Client.Type.NORMAL, 40, 15, 10)
        claim2 = self.create_claim(self.a_transit(2), 39)
        result2 = resolver.resolve(claim2, Client.Type.NORMAL, 40, 15, 10)
        claim3 = self.create_claim(self.a_transit(3), 39)
        result3 = resolver.resolve(claim3, Client.Type.NORMAL, 40, 15, 10)

        # when
        claim4 = self.create_claim(self.a_transit(4), 41)
        result4: ClaimsResolver.Result = resolver.resolve(claim4, Client.Type.NORMAL, 40, 4, 10)

        # then
        self.assertEqual(Status.REFUNDED, result1.decision)
        self.assertEqual(Status.REFUNDED, result2.decision)
        self.assertEqual(Status.REFUNDED, result3.decision)
        self.assertEqual(Status.ESCALATED, result4.decision)

        self.assertEqual(ClaimsResolver.WhoToAsk.ASK_NOONE, result1.who_to_ask)
        self.assertEqual(ClaimsResolver.WhoToAsk.ASK_NOONE, result2.who_to_ask)
        self.assertEqual(ClaimsResolver.WhoToAsk.ASK_NOONE, result3.who_to_ask)

    def test_low_cost_transits_are_refunded_when_many_transits(self):
        # given
        resolver = ClaimsResolver()
        # and
        claim = self.create_claim(self.a_transit(1), 39)
        resolver.resolve(claim, Client.Type.NORMAL, 40, 15, 10)
        claim2 = self.create_claim(self.a_transit(2), 39)
        resolver.resolve(claim2, Client.Type.NORMAL, 40, 15, 10)
        claim3 = self.create_claim(self.a_transit(3), 39)
        resolver.resolve(claim3, Client.Type.NORMAL, 40, 15, 10)
        # and
        claim4 = self.create_claim(self.a_transit(4), 39)

        # when
        result: ClaimsResolver.Result = resolver.resolve(claim4, Client.Type.NORMAL, 40, 10, 9)

        # then
        self.assertEqual(Status.REFUNDED, result.decision)
        self.assertEqual(ClaimsResolver.WhoToAsk.ASK_NOONE, result.who_to_ask)

    def test_high_cost_transits_are_escalated_even_with_many_transits(self):
        # given
        resolver = ClaimsResolver()
        # and
        claim = self.create_claim(self.a_transit(1), 39)
        resolver.resolve(claim, Client.Type.NORMAL, 40, 15, 10)
        claim2 = self.create_claim(self.a_transit(2), 39)
        resolver.resolve(claim2, Client.Type.NORMAL, 40, 15, 10)
        claim3 = self.create_claim(self.a_transit(3), 39)
        resolver.resolve(claim3, Client.Type.NORMAL, 40, 15, 10)
        # and
        claim4 = self.create_claim(self.a_transit(4), 50)

        # when
        result: ClaimsResolver.Result = resolver.resolve(claim4, Client.Type.NORMAL, 40, 12, 10)

        # then
        self.assertEqual(Status.ESCALATED, result.decision)
        self.assertEqual(ClaimsResolver.WhoToAsk.ASK_CLIENT, result.who_to_ask)

    def test_high_cost_transits_are_escalated_when_few_transits(self):
        # given
        resolver = ClaimsResolver()
        # and
        claim = self.create_claim(self.a_transit(1), 39)
        resolver.resolve(claim, Client.Type.NORMAL, 40, 15, 10)
        claim2 = self.create_claim(self.a_transit(2), 39)
        resolver.resolve(claim2, Client.Type.NORMAL, 40, 15, 10)
        claim3 = self.create_claim(self.a_transit(3), 39)
        resolver.resolve(claim3, Client.Type.NORMAL, 40, 15, 10)
        # and
        claim4 = self.create_claim(self.a_transit(4), 50)

        # when
        result: ClaimsResolver.Result = resolver.resolve(claim4, Client.Type.NORMAL, 40, 2, 10)

        # then
        self.assertEqual(Status.ESCALATED, result.decision)
        self.assertEqual(ClaimsResolver.WhoToAsk.ASK_DRIVER, result.who_to_ask)

    def a_transit(self, transit_id: int) -> Transit:
        return Transit(id=transit_id)

    def create_claim(self, transit: Transit, transit_price: int) -> Claim:
        claim = Claim()
        claim.set_transit(transit.id)
        claim.set_transit_price(Money(transit_price))
        claim.owner_id = 1
        return claim

    def a_client(self, client_type: Client.Type) -> Client:
        client = Client()
        client.type = client_type
        return client
