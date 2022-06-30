from typing import Type, Any

from common.functional import BiFunction
from contracts.model.document_header import DocumentHeader
from contracts.model.state.dynamic.change_command import ChangeCommand
from contracts.model.state.dynamic.config.events.document_event import DocumentEvent


class PublishEvent(BiFunction[DocumentHeader, ChangeCommand, None]):
    __event_class: Type[DocumentEvent]

    publisher: Any

    def __init__(self, event_class: Type[DocumentEvent], publisher: Any):
        self.__event_class = event_class
        self.publisher = publisher

    def apply(self, document_header: DocumentHeader, command: ChangeCommand) -> None:
        event: DocumentEvent
        try:
            event = self.__event_class(
                document_header.id,
                document_header.state_descriptor,
                document_header.get_content_id(),
                document_header.get_document_number(),
            )
        except Exception as e:
            raise e

        self.publisher.publish_event(event)

        return None
