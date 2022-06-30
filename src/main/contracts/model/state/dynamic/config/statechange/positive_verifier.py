from __future__ import annotations

from common.functional import BiFunction
from contracts.model.state.dynamic.change_command import ChangeCommand


class PositiveVerifier(BiFunction['State', ChangeCommand, bool]):

    def apply(self, state: State, command: ChangeCommand = None) -> bool:
        return True
