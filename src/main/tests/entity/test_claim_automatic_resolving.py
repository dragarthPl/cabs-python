from unittest import TestCase

from entity import Claim, ClaimsResolver, Transit, Client
from money import Money


class TestClaimAutomaticResolving(TestCase):
    def test_second_claim_for_the_same_transit_will_be_escalated(self):
        # given
        resolver = ClaimsResolver()
        # and
        transit = self.a_transit(1, 39)
        # and
        claim: Claim = self.create_claim(transit)
        # and
        resolver.resolve(claim, 40, 15, 10)
        # and
        claim2: Claim = self.create_claim(transit)

        # when
        result: ClaimsResolver.Result = resolver.resolve(claim2, 40, 15, 10)

        # then
        self.assertEqual(Claim.Status.ESCALATED, result.decision)
        self.assertEqual(ClaimsResolver.WhoToAsk.ASK_NOONE, result.who_to_ask)

    def test_low_cost_transits_are_refunded_if_client_is_vip(self):
        # given
        resolver = ClaimsResolver()
        # and
        transit = self.a_transit(1, 39)
        # and
        claim: Claim = self.create_claim(transit)

        # when
        result: ClaimsResolver.Result = resolver.resolve(claim, 40, 15, 10)

        # then
        self.assertEqual(Claim.Status.REFUNDED, result.decision)
        self.assertEqual(ClaimsResolver.WhoToAsk.ASK_NOONE, result.who_to_ask)

    def test_high_cost_transits_are_escalated_even_when_client_is_vip(self):
        # given
        resolver = ClaimsResolver()
        # and
        claim = self.create_claim(self.a_transit(1, 39))
        resolver.resolve(claim, 40, 15, 10)
        claim2 = self.create_claim(self.a_transit(2, 39))
        resolver.resolve(claim2, 40, 15, 10)
        claim3 = self.create_claim(self.a_transit(3, 39))
        resolver.resolve(claim3, 40, 15, 10)
        # and
        claim4 = self.create_client_claim(self.a_transit(4, 41), self.a_client(Client.Type.VIP))

        # when
        result: ClaimsResolver.Result = resolver.resolve(claim4, 40, 15, 10)

        # then
        self.assertEqual(Claim.Status.ESCALATED, result.decision)
        self.assertEqual(ClaimsResolver.WhoToAsk.ASK_DRIVER, result.who_to_ask)

    def test_first_three_claims_are_refunded(self):
        # given
        resolver = ClaimsResolver()
        # and
        claim = self.create_claim(self.a_transit(1, 39))
        result1 = resolver.resolve(claim, 40, 15, 10)
        claim2 = self.create_claim(self.a_transit(2, 39))
        result2 = resolver.resolve(claim2, 40, 15, 10)
        claim3 = self.create_claim(self.a_transit(3, 39))
        result3 = resolver.resolve(claim3, 40, 15, 10)

        # when
        claim4 = self.create_client_claim(self.a_transit(4, 41), self.a_client(Client.Type.NORMAL))
        result4: ClaimsResolver.Result = resolver.resolve(claim4, 40, 4, 10)

        # then
        self.assertEqual(Claim.Status.REFUNDED, result1.decision)
        self.assertEqual(Claim.Status.REFUNDED, result2.decision)
        self.assertEqual(Claim.Status.REFUNDED, result3.decision)
        self.assertEqual(Claim.Status.ESCALATED, result4.decision)

        self.assertEqual(ClaimsResolver.WhoToAsk.ASK_NOONE, result1.who_to_ask)
        self.assertEqual(ClaimsResolver.WhoToAsk.ASK_NOONE, result2.who_to_ask)
        self.assertEqual(ClaimsResolver.WhoToAsk.ASK_NOONE, result3.who_to_ask)

    def test_low_cost_transits_are_refunded_when_many_transits(self):
        # given
        resolver = ClaimsResolver()
        # and
        claim = self.create_claim(self.a_transit(1, 39))
        resolver.resolve(claim, 40, 15, 10)
        claim2 = self.create_claim(self.a_transit(2, 39))
        resolver.resolve(claim2, 40, 15, 10)
        claim3 = self.create_claim(self.a_transit(3, 39))
        resolver.resolve(claim3, 40, 15, 10)
        # and
        claim4 = self.create_client_claim(self.a_transit(4, 39), self.a_client(Client.Type.NORMAL))

        # when
        result: ClaimsResolver.Result = resolver.resolve(claim4, 40, 10, 9)

        # then
        self.assertEqual(Claim.Status.REFUNDED, result.decision)
        self.assertEqual(ClaimsResolver.WhoToAsk.ASK_NOONE, result.who_to_ask)

    def test_high_cost_transits_are_escalated_even_with_many_transits(self):
        # given
        resolver = ClaimsResolver()
        # and
        claim = self.create_claim(self.a_transit(1, 39))
        resolver.resolve(claim, 40, 15, 10)
        claim2 = self.create_claim(self.a_transit(2, 39))
        resolver.resolve(claim2, 40, 15, 10)
        claim3 = self.create_claim(self.a_transit(3, 39))
        resolver.resolve(claim3, 40, 15, 10)
        # and
        claim4 = self.create_client_claim(self.a_transit(4, 50), self.a_client(Client.Type.NORMAL))

        # when
        result: ClaimsResolver.Result = resolver.resolve(claim4, 40, 12, 10)

        # then
        self.assertEqual(Claim.Status.ESCALATED, result.decision)
        self.assertEqual(ClaimsResolver.WhoToAsk.ASK_CLIENT, result.who_to_ask)

    def test_high_cost_transits_are_escalated_when_few_transits(self):
        # given
        resolver = ClaimsResolver()
        # and
        claim = self.create_claim(self.a_transit(1, 39))
        resolver.resolve(claim, 40, 15, 10)
        claim2 = self.create_claim(self.a_transit(2, 39))
        resolver.resolve(claim2, 40, 15, 10)
        claim3 = self.create_claim(self.a_transit(3, 39))
        resolver.resolve(claim3, 40, 15, 10)
        # and
        claim4 = self.create_client_claim(self.a_transit(4, 50), self.a_client(Client.Type.NORMAL))

        # when
        result: ClaimsResolver.Result = resolver.resolve(claim4, 40, 2, 10)

        # then
        self.assertEqual(Claim.Status.ESCALATED, result.decision)
        self.assertEqual(ClaimsResolver.WhoToAsk.ASK_DRIVER, result.who_to_ask)

    def a_transit(self, transit_id: int, price: int) -> Transit:
        transit: Transit = Transit(id=transit_id)
        transit.set_price(Money(price))
        return transit

    def create_claim(self, transit: Transit) -> Claim:
        claim = Claim()
        claim.set_transit(transit.id)
        claim.set_transit_price(transit.get_price())
        return claim

    def create_client_claim(self, transit: Transit, client: Client) -> Claim:
        claim = Claim()
        claim.set_transit(transit.id)
        claim.set_transit_price(transit.get_price())
        claim.owner_id = client.id
        claim.owner = client
        return claim

    def a_client(self, client_type: Client.Type) -> Client:
        client = Client()
        client.type = client_type
        return client