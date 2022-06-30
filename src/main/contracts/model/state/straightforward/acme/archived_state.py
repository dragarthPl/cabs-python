from contracts.model.document_header import DocumentHeader
from contracts.model.state.straightforward.base_state import BaseState


class ArchivedState(BaseState):
    def can_change_content(self) -> bool:
        return False

    def state_after_content_change(self) -> 'BaseState':
        return self

    def can_change_from(self, previous_state: 'BaseState'):
        return True

    def acquire(self, document_header: DocumentHeader) -> None:
        ...
