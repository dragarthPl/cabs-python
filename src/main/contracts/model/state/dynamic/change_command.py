from typing import Any, Dict, Generic, TypeVar, Type

T = TypeVar('T')


class ChangeCommand:
    __desired_state: str
    __params: Dict[str, Any]

    def __init__(
            self,
            desired_state: str,
            params: Dict[str, Any] = None,
    ):
        self.__desired_state = desired_state
        self.__params = params or {}

    def with_param(self, name: str, value: Any) -> 'ChangeCommand':
        self.__params[name] = value
        return self

    def get_param(self, name: str, type_param: Type[T]) -> Generic[T]:
        return self.__params.get(name)

    def to_string(self):
        return f"ChangeCommand{{desiredState='{self.__desired_state}'}}"

    def __str__(self):
        return self.to_string()

    @property
    def desired_state(self):
        return self.__desired_state
