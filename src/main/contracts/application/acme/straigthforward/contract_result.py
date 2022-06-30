import enum

from contracts.model.content.document_number import DocumentNumber


class ContractResult:
    class Result(enum.Enum):
        FAILURE = enum.auto()
        SUCCESS = enum.auto()

    __result: Result
    __document_header_id: int
    __document_number: DocumentNumber
    __state_descriptor: str

    def __init__(
            self,
            result: Result,
            document_header_id: int,
            document_number: DocumentNumber,
            state_descriptor: str,
    ):
        self.__result = result
        self.__document_header_id = document_header_id
        self.__document_number = document_number
        self.__state_descriptor = state_descriptor

    @property
    def result(self):
        return self.__result

    @property
    def document_number(self):
        return self.__document_number

    @property
    def document_header_id(self):
        return self.__document_header_id

    @property
    def state_descriptor(self):
        return self.__state_descriptor
