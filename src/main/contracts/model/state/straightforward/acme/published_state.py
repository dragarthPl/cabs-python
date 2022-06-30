from contracts.model.document_header import DocumentHeader
from contracts.model.state.straightforward.acme.verified_state import VerifiedState
from contracts.model.state.straightforward.base_state import BaseState


class PublishedState(BaseState):

    def can_change_content(self) -> bool:
        return False

    def state_after_content_change(self) -> 'BaseState':
        return self

    def can_change_from(self, previous_state: 'BaseState'):
        return isinstance(previous_state, VerifiedState) and previous_state.document_header.not_empty()

    def acquire(self, document_header: DocumentHeader) -> None:
        ...
