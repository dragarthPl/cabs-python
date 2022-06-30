from typing import Dict, List, Callable, Any, Optional

from common.functional import Predicate, BiFunction
from contracts.model.content_id import ContentId
from contracts.model.document_header import DocumentHeader
from contracts.model.state.dynamic.change_command import ChangeCommand
from contracts.model.state.dynamic.config.predicates.contentchange.negative_predicate import NegativePredicate
from contracts.model.state.dynamic.config.statechange.positive_verifier import PositiveVerifier


class State:
    """
    Unique name of a state
    """
    __state_descriptor: str

    # TODO consider to get rid of this stateful object and transform State to reusable logic
    __document_header: DocumentHeader

    # TODO consider merging contentChangePredicate and afterContentChangeState int one function

    """
    predicates tested if content can be changed
    """
    __content_change_predicate: Predicate['State'] = NegativePredicate()

    """
    state after content change - may be the same as before content change
    """
    __after_content_change_state: 'State'

    """
    possible transitions to other states with rules that need to be tested to determine if transition is legal
    """
    __state_change_predicates: Dict['State', List[BiFunction['State', ChangeCommand, bool]]]

    """
    actions that may be needed to perform while transition to the next state
    """
    __after_state_change_actions: List[BiFunction[DocumentHeader, ChangeCommand, None]]

    def __init__(self, state_descriptor: str):
        self.__state_descriptor = state_descriptor
        self.__state_change_predicates = {}
        self.__after_state_change_actions = []
        self.__after_content_change_state = None
        self.add_state_change_predicates(self, [PositiveVerifier()])  # change to self is always possible

    def init(self, document_header: DocumentHeader) -> None:
        self.__document_header = document_header
        document_header.state_descriptor = self.__state_descriptor

    def change_content(self, current_content: ContentId) -> 'State':
        if not self.is_content_editable():
            return self

        new_state: State = self.__after_content_change_state  # local variable just to focus attention
        if new_state.__content_change_predicate.test(self):
            new_state.init(document_header=self.__document_header)
            self.__document_header.change_current_content(current_content)
            return new_state

        return self

    def change_state(self, command: ChangeCommand):
        desired_state: State = self.__find(command.desired_state)

        if not desired_state:
            return self

        predicates: List[BiFunction[State, ChangeCommand, bool]] = self.state_change_predicates.get(desired_state, [])

        if all(list(map(lambda e: e.apply(self, command), predicates))):
            desired_state.init(self.__document_header)
            [e.apply(self.__document_header, command) for e in desired_state.__after_state_change_actions]
            return desired_state

        return self

    @property
    def state_descriptor(self) -> str:
        return self.__state_descriptor

    @property
    def document_header(self) -> DocumentHeader:
        return self.__document_header

    @property
    def state_change_predicates(self) -> Dict['State', List[BiFunction['State', ChangeCommand, bool]]]:
        return self.__state_change_predicates

    @property
    def content_change_predicate(self) -> Predicate['State']:
        return self.__content_change_predicate

    @content_change_predicate.setter
    def content_change_predicate(self, predicate: Predicate['State']):
        self.__content_change_predicate = predicate

    def is_content_editable(self):
        return self.__after_content_change_state is not None

    def __str__(self) -> str:
        return self.to_string()

    def to_string(self) -> str:
        return f"State{{stateDescriptor='{self.__state_descriptor}'}}"

    def add_state_change_predicates(
        self,
        to_state: 'State',
        predicates_to_add: List[BiFunction['State', ChangeCommand, bool]],
    ):
        if to_state in self.__state_change_predicates:
            predicates = self.__state_change_predicates.get(to_state)
            predicates.extend(predicates_to_add)
        else:
            self.__state_change_predicates[to_state] = predicates_to_add

    def add_after_state_change_action(self, action: BiFunction[DocumentHeader, ChangeCommand, None]):
        self.__after_state_change_actions.append(action)

    def set_after_content_change_state(self, to_state: 'State'):
        self.__after_content_change_state = to_state

    def set_content_change_predicate(self, predicate: Predicate['State']):
        self.__content_change_predicate = predicate

    def __find(self, desired_state: str) -> Optional['State']:
        return next(filter(
            lambda e: e.state_descriptor == desired_state,
            self.__state_change_predicates.keys()
        ), None)
