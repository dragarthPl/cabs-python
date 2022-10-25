import enum
import json
from typing import Optional, Set

from common.base_entity import BaseEntity
from crm.claims.claim import Claim
from crm.claims.status import Status
from entity import Client


class WhoToAsk(enum.Enum):
    ASK_DRIVER = 1
    ASK_CLIENT = 2
    ASK_NOONE = 3


class ClaimsResolver(BaseEntity, table=True):
    __table_args__ = {'extend_existing': True}

    WhoToAsk = WhoToAsk

    class Result:
        who_to_ask: WhoToAsk
        decision: Status

        def __init__(self, who_to_ask: WhoToAsk, decision: Status):
            self.who_to_ask = who_to_ask
            self.decision = decision

    client_id: Optional[int] = None
    claimed_transits_ids: str = ""

    def resolve(
        self,
        claim: Claim,
        client_type: Client.Type,
        automatic_refund_for_vip_threshold: float,
        number_of_transits: int,
        no_of_transits_for_claim_automatic_refund: int,
    ) -> Result:
        transit_id = claim.transit_id
        if str(transit_id) in self.claimed_transits_ids:
            return self.Result(WhoToAsk.ASK_NOONE, Status.ESCALATED)
        self.add_new_claim_for(claim.transit_id)
        if self.number_of_claims() <= 3:
            return self.Result(WhoToAsk.ASK_NOONE, Status.REFUNDED)
        if client_type == Client.Type.VIP:
            if claim.get_transit_price().to_int() < automatic_refund_for_vip_threshold:
                return self.Result(WhoToAsk.ASK_NOONE, Status.REFUNDED)
            else:
                return self.Result(WhoToAsk.ASK_DRIVER, Status.ESCALATED)
        else:
            if (number_of_transits >= no_of_transits_for_claim_automatic_refund):
                if claim.get_transit_price().to_int() < automatic_refund_for_vip_threshold:
                    return self.Result(WhoToAsk.ASK_NOONE, Status.REFUNDED)
                else:
                    return self.Result(WhoToAsk.ASK_CLIENT, Status.ESCALATED)
            else:
                return self.Result(WhoToAsk.ASK_DRIVER, Status.ESCALATED)

    def add_new_claim_for(self, transit_id: int):
        transits_ids = self.get_claimed_transits_ids()
        transits_ids.add(transit_id)
        self.claimed_transits_ids = json.dumps(list(transits_ids))

    def get_claimed_transits_ids(self) -> Set[int]:
        if self.claimed_transits_ids:
            return set(json.loads(self.claimed_transits_ids))
        else:
            return set()

    def number_of_claims(self) -> int:
        return len(self.get_claimed_transits_ids())
