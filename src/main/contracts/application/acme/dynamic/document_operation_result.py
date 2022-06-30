import enum
from typing import List, Dict

from contracts.model.content.document_number import DocumentNumber
from contracts.model.content_id import ContentId


class DocumentOperationResult:
    class Result(enum.Enum):
        SUCCESS = enum.auto()
        ERROR = enum.auto()

    __result: Result
    __state_name: str
    __content_id: ContentId
    __document_header_id: int
    __document_number: DocumentNumber

    __possible_transitions_and_rules: Dict[str, List[str]]
    __content_change_possible: bool
    __content_change_predicate: str

    def __init__(
            self,
            result: Result,
            document_header_id: int,
            document_number: DocumentNumber,
            state_name: str,

            content_id: ContentId,
            possible_transitions_and_rules: Dict[str, List[str]],
            content_change_possible: bool,
            content_change_predicate: str
    ):
        self.__result = result
        self.__document_header_id = document_header_id
        self.__document_number = document_number
        self.__state_name = state_name
        self.__content_id = content_id
        self.__possible_transitions_and_rules = possible_transitions_and_rules
        self.__content_change_possible = content_change_possible
        self.__content_change_predicate = content_change_predicate

    @property
    def possible_transitions_and_rules(self) -> Dict[str, List[str]]:
        return self.__possible_transitions_and_rules

    @property
    def content_change_predicate(self) -> str:
        return self.__content_change_predicate

    def is_content_change_possible(self):
        return self.__content_change_possible

    @property
    def result(self):
        return self.__result

    @property
    def state_name(self):
        return self.__state_name

    @property
    def document_number(self):
        return self.__document_number

    @property
    def document_header_id(self):
        return self.__document_header_id

    @property
    def content_id(self):
        return self.__content_id
