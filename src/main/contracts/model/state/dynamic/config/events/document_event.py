from abc import ABCMeta

from common.application_event_publisher import ApplicationEvent
from contracts.model.content.document_number import DocumentNumber
from contracts.model.content_id import ContentId


class DocumentEvent(ApplicationEvent, metaclass=ABCMeta):
    __document_id: int
    __current_sate: str
    __content_id: ContentId
    __number: DocumentNumber

    class Config:
        arbitrary_types_allowed = True

    def __init__(
        self,
        document_id: int,
        current_sate: str,
        content_id: ContentId,
        number: DocumentNumber,
    ):
        super().__init__(number)
        self.__document_id = document_id
        self.__current_sate = current_sate
        self.__content_id = content_id
        self.__number = number

    @property
    def document_id(self) -> int:
        return self.__document_id

    @property
    def current_sate(self) -> str:
        return self.__current_sate

    @property
    def content_id(self) -> ContentId:
        return self.__content_id

    @property
    def number(self) -> DocumentNumber:
        return self.__number
