from contracts.model.document_header import DocumentHeader
from contracts.model.state.straightforward.acme.draft_state import DraftState
from contracts.model.state.straightforward.base_state import BaseState


class VerifiedState(BaseState):
    __verifier_id: int

    def __init__(self, verifier_id: int):
        self.__verifier_id = verifier_id

    def can_change_content(self) -> bool:
        return True

    def state_after_content_change(self) -> 'BaseState':
        return DraftState()

    def can_change_from(self, previous_state: 'BaseState'):
        return (
            isinstance(previous_state, DraftState)
            and previous_state.document_header.author_id != self.__verifier_id
            and previous_state.document_header.not_empty()
        )

    def acquire(self, document_header: DocumentHeader) -> None:
        document_header.verifier_id = self.__verifier_id
