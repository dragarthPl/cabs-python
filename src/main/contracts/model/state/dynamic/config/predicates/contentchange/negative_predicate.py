from __future__ import annotations

from common.functional import Predicate


class NegativePredicate(Predicate['State']):

    def test(self, state: State) -> bool:
        return False
