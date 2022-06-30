from common.functional import BiFunction
from contracts.model.state.dynamic.change_command import ChangeCommand
from contracts.model.state.dynamic.config.actions.change_verifier import ChangeVerifier
from contracts.model.state.dynamic.state import State


class AuthorIsNotAVerifier(BiFunction[State, ChangeCommand, bool]):
    PARAM_VERIFIER: str = ChangeVerifier.PARAM_VERIFIER

    def apply(self, state: State, command: ChangeCommand = None) -> bool:
        return not command.get_param(self.PARAM_VERIFIER, int) == state.document_header.author_id
