from typing import Optional
from uuid import UUID

from contracts.model.content.content_version import ContentVersion


class DocumentDTO:
    __content_id: UUID
    __physical_content: str
    __content_version: ContentVersion

    def __init__(self, content_id: Optional[UUID], physical_content: str, content_version: ContentVersion):
        self.__content_id = content_id
        self.__physical_content = physical_content
        self.__content_version = content_version

    @property
    def content_id(self) -> UUID:
        return self.__content_id

    @property
    def physical_content(self) -> str:
        return self.__physical_content

    @property
    def content_version(self) -> ContentVersion:
        return self.__content_version
