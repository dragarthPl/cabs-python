import random
import sys
from typing import Any, Optional

from contracts.legacy.document import Document
from contracts.legacy.document_status import DocumentStatus
from contracts.legacy.unsupported_transition_exception import UnsupportedTransitionException
from contracts.legacy.user import User
from contracts.legacy.versionable import Versionable


class Contract2(Document, Versionable):

    def __init__(self, number: str, creator: User, **data: Any):
        super().__init__(number, creator, **data)

    def publish(self) -> None:
        raise UnsupportedTransitionException(self.status, DocumentStatus.PUBLISHED)

    def accept(self):
        if self.status == DocumentStatus.VERIFIED:
            self.status = DocumentStatus.PUBLISHED  # reusing unused enum to provide data model for new status

    # Contracts just don't have a title, it's just a part of the content
    def change_title(self, title: str):
        super().change_title(title + self.content)

    # NOT @Override
    def change_content(self, content: str, user_status: Optional[str] = None) -> None:
        if user_status == "ChiefSalesOfficerStatus" or self.__mister_vladimir_is_logged_in(user_status):
            self.override_published = True
            self.change_content(content)

    def __mister_vladimir_is_logged_in(self, user_status: str):
        return user_status.lower().strip() == f"!!!id={self.NUMBER_OF_THE_BEAST}"

    NUMBER_OF_THE_BEAST: str = "616"

    def recreate_to(self, version: int):
        # TODO need to learn Kafka
        pass

    def get_last_version(self):
        return random.randint(0, sys.maxsize)
