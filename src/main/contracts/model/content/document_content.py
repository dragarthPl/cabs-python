import uuid

from typing import Any, Optional

from sqlalchemy.orm import composite
from sqlmodel import SQLModel, Field

from common.base_entity import new_uuid
from contracts.model.content.content_version import ContentVersion


class DocumentContent(SQLModel, table=True):
    __table_args__ = {'extend_existing': True}

    id: uuid.UUID = Field(
        default_factory=new_uuid,
        nullable=False,
        primary_key=True
    )

    previous_id: Optional[uuid.UUID]

    physical_content: str  # some kind of reference to file, version control. In sour sample i will be a blob stored
    # in DB:)

    content_version: str
    __content_version: composite(ContentVersion, 'content_version')  # just a human readable descriptor

    class Config:
        arbitrary_types_allowed = True

    def __init__(
        self,
        previous_id: uuid.UUID,
        content_version: ContentVersion,
        physical_content: str, **data: Any
    ):
        super().__init__(**data)
        self.previous_id = previous_id
        self.content_version = content_version.content_version
        self.physical_content = physical_content

    def get_document_version(self) -> ContentVersion:
        return self.__content_version
