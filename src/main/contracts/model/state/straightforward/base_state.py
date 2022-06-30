from abc import ABCMeta, abstractmethod

from contracts.model.content_id import ContentId
from contracts.model.document_header import DocumentHeader

# TODO introduce an interface

class BaseState(metaclass=ABCMeta):
    _document_header: DocumentHeader

    def init(self, document_header: DocumentHeader):
        self._document_header = document_header
        document_header.state_descriptor = self.get_state_descriptor()

    def change_content(self, current_content: ContentId) -> 'BaseState':
        if self.can_change_content():
            new_state: BaseState = self.state_after_content_change()
            new_state.init(self._document_header)
            self._document_header.change_current_content(current_content)
            new_state.acquire(self._document_header)
            return new_state
        return self

    @abstractmethod
    def can_change_content(self) -> bool:
        ...

    @abstractmethod
    def state_after_content_change(self) -> 'BaseState':
        ...

    def change_state(self, new_state: 'BaseState') -> 'BaseState':
        if new_state.can_change_from(self):
            new_state.init(self._document_header)
            self._document_header.state_descriptor = new_state.get_state_descriptor()
            new_state.acquire(self._document_header)
            return new_state

        return self

    def get_state_descriptor(self):
        return f"{self.__class__.__module__}.{self.__class__.__name__}"

    @abstractmethod
    def acquire(self, document_header: DocumentHeader) -> None:
        ...

    @abstractmethod
    def can_change_from(self, previous_state: 'BaseState') -> bool:
        ...

    @property
    def document_header(self):
        return self._document_header
