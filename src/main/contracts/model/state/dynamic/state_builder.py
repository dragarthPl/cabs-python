import enum
from typing import Dict, List, Callable

from common.functional import BiFunction
from contracts.model.document_header import DocumentHeader
from contracts.model.state.dynamic.change_command import ChangeCommand
from contracts.model.state.dynamic.config.predicates.contentchange.positive_predicate import PositivePredicate
from contracts.model.state.dynamic.config.statechange.previous_state_verifier import PreviousStateVerifier
from contracts.model.state.dynamic.state import State
from contracts.model.state.dynamic.state_config import StateConfig


class StateBuilder(StateConfig):
    class FinalStateConfig:
        __state: State

        def __init__(self, state: State):
            self.__state = state

        """
        Adds an operation to be performed if state have changed
        """
        def action(self, action: BiFunction[DocumentHeader, ChangeCommand, None]):
            self.__state.add_after_state_change_action(action)
            return self

    class Mode(enum.Enum):
        """
        Rules for state transition {@link #check(BiFunction) check}  method called or {@link #from(String) from}  method called
        """
        STATE_CHANGE = 1
        """
        Rules for content change {@link #whenContentChanged() whenContentChanged}  method called
        """
        CONTENT_CHANGE = 2

    __mode: Mode

    # all states configured so far
    __states: Dict[str, State]

    __from_state: State
    __initial_state: State = None
    __predicates: List[BiFunction[State, ChangeCommand, bool]]

    def __init__(self):
        self.__states = {}

    # ========= methods for application layer - business process

    def begin(self, document_header: DocumentHeader) -> State:
        document_header.state_descriptor = self.__initial_state.state_descriptor
        return self.recreate(document_header)

    def recreate(self, document_header: DocumentHeader) -> State:
        state: State = self.__states.get(document_header.state_descriptor)
        state.init(document_header)
        return state

    # ======= methods for assembling process

    def begin_with(self, state_name: str) -> 'StateBuilder':
        if self.__initial_state:
            raise AttributeError(f"Initial state already set to: {self.__initial_state.state_descriptor}")

        config: StateBuilder = self.from_name(state_name)
        self.__initial_state = self.__from_state
        return config

    def from_name(self, state_name: str) -> 'StateBuilder':
        self.__mode = self.Mode.STATE_CHANGE
        self.__predicates = []
        self.__from_state = self.get_or_put(state_name)
        return self

    def check(self, checking_function: BiFunction[State, ChangeCommand, bool]) -> 'StateBuilder':
        self.__mode = self.Mode.STATE_CHANGE
        self.__predicates.append(checking_function)
        return self

    def to(self, state_name: str) -> FinalStateConfig:
        to_state: State = self.get_or_put(state_name)

        match self.__mode:
            case self.Mode.STATE_CHANGE:
                self.__predicates.append(PreviousStateVerifier(self.__from_state.state_descriptor))
                self.__from_state.add_state_change_predicates(to_state, self.__predicates)
            case self.Mode.CONTENT_CHANGE:
                self.__from_state.set_after_content_change_state(to_state)
                to_state.content_change_predicate = PositivePredicate()

        self.__predicates = None
        self.__from_state = None
        self.__mode = None

        return self.FinalStateConfig(to_state)

    def when_content_changed(self) -> 'StateBuilder':
        self.__mode = self.Mode.CONTENT_CHANGE
        return self

    def get_or_put(self, state_name: str) -> State:
        if state_name not in self.__states:
            self.__states[state_name] = State(state_name)
        return self.__states.get(state_name)
