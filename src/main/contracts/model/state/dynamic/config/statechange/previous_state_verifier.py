from common.functional import BiFunction
from contracts.model.state.dynamic.change_command import ChangeCommand
from contracts.model.state.dynamic.state import State


class PreviousStateVerifier(BiFunction[State, ChangeCommand, bool]):
    __state_descriptor: str

    def __init__(self, state_descriptor: str):
        self.__state_descriptor = state_descriptor

    def apply(self, state: State, command: ChangeCommand = None) -> bool:
        return state.state_descriptor == self.__state_descriptor
