from contracts.model.content.document_number import DocumentNumber
from contracts.model.content_id import ContentId
from contracts.model.state.dynamic.config.events.document_event import DocumentEvent


class DocumentUnpublished(DocumentEvent):
    def __init__(self, document_id: int, current_sate: str, content_id: ContentId, number: DocumentNumber):
        super().__init__(document_id, current_sate, content_id, number)
