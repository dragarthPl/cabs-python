from common.functional import BiFunction
from contracts.model.state.dynamic.change_command import ChangeCommand
from contracts.model.state.dynamic.state import State


class ContentNotEmptyVerifier(BiFunction[State, ChangeCommand, bool]):

    def apply(self, state: State, command: ChangeCommand = None) -> bool:
        return state.document_header.content_id is not None
