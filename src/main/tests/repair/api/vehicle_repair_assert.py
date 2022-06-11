from typing import Set, List
from unittest import TestCase

from money import Money
from party.api.party_id import PartyId
from repair.api.resolve_result import ResolveResult
from repair.legacy.parts.parts import Parts


class VehicleRepairAssert(TestCase):
    result: ResolveResult

    def __init__(self, result: ResolveResult, demand_success: bool = True):
        super().__init__()
        self.result = result
        if demand_success:
            self.assertEqual(ResolveResult.Status.SUCCESS, result.status)
        else:
            self.assertEqual(ResolveResult.Status.ERROR, result.status)

    def free(self) -> 'VehicleRepairAssert':
        self.assertEqual(Money.ZERO, self.result.total_cost)
        return self

    def all_parts(self, parts: Set[Parts]) -> 'VehicleRepairAssert':
        self.assertEqual(parts, self.result.accepted_parts)
        return self

    def by(self, handling_party: PartyId):
        self.assertEqual(handling_party.to_uuid(), self.result.handling_party)
        return self

    def all_parts_but(self, parts: Set[Parts], excluded_parts: List[Parts]):
        exptected_parts: Set[Parts] = set(parts)
        exptected_parts.difference_update(excluded_parts)

        self.assertEqual(exptected_parts, self.result.accepted_parts)
        return self
