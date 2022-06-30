from __future__ import annotations

from abc import ABCMeta, abstractmethod


class StateConfig(metaclass=ABCMeta):
    @abstractmethod
    def begin(self, document_header: DocumentHeader) -> State:
        ...

    @abstractmethod
    def recreate(self, document_header: DocumentHeader) -> State:
        ...
