from __future__ import annotations

from common.functional import Predicate
from contracts.model.state.dynamic.state import State


class PositivePredicate(Predicate[State]):

    def test(self, state: State) -> bool:
        return True
