from typing import Set
from uuid import UUID

from money import Money
from repair.legacy.parts.parts import Parts


class RepairingResult:
    handling_party: UUID
    total_cost: Money
    handled_parts: Set[Parts]

    def __init__(self, handling_party: UUID, total_cost: Money, handled_parts: Set[Parts]):
        self.handling_party = handling_party
        self.total_cost = total_cost
        self.handled_parts = handled_parts
