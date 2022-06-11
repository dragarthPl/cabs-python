from typing import Set, Optional
from uuid import UUID

from money import Money
from repair.legacy.parts.parts import Parts


class ResolveResult:
    class Status:
        SUCCESS = 1
        ERROR = 2

    handling_party: UUID
    total_cost: Optional[Money]
    accepted_parts: Optional[Set[Parts]]
    status: Optional[Status]

    def __init__(
        self,
        status: Status,
        handling_party: Optional[UUID] = None,
        total_cost: Optional[Money] = None,
        accepted_parts: Optional[Set[Parts]] = None,
    ):
        self.status = status
        self.handling_party = handling_party
        self.total_cost = total_cost
        self.accepted_parts = accepted_parts
