import enum
from typing import Optional
from uuid import UUID


class CommitResult:
    class Result(enum.Enum):
        FAILURE = enum.auto()
        SUCCESS = enum.auto()

    __content_id: UUID
    __result: Result
    __message: Optional[str]

    def __init__(self,  content_id: UUID, result: Result, message: Optional[str] = None):
        self.__content_id = content_id
        self.__result = result
        self.__message = message

    @property
    def result(self):
        return self.__result

    @property
    def content_id(self):
        return self.__content_id
