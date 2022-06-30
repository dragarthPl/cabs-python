from typing import Any, Optional

from common.base_entity import BaseEntity
from contracts.model.content.document_number import DocumentNumber
from contracts.model.content_id import ContentId
from sqlalchemy.orm import composite


class DocumentHeader(BaseEntity, table=True):
    __table_args__ = {'extend_existing': True}

    number: str
    __number: Optional[DocumentNumber] = composite(DocumentNumber, 'number')

    author_id: Optional[int]

    verifier_id: Optional[int]

    state_descriptor: Optional[str]

    content_id: Optional[str]
    __content_id: Optional[ContentId] = composite(ContentId, 'content_id')

    class Config:
        arbitrary_types_allowed = True

    def __init__(self, author_id: int, number: DocumentNumber, **data: Any):
        super().__init__(**data)
        self.author_id = author_id
        self.number = number.number

    def change_current_content(self, content_id: ContentId) -> None:
        self.content_id = str(content_id.content_id)

    def not_empty(self):
        return self.content_id is not None

    def get_content_id(self) -> ContentId:
        return self.__content_id

    def get_document_number(self) -> DocumentNumber:
        return self.__number

    def get_verifier(self):
        return self.verifier_id
