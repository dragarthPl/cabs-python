import sys
import random
from typing import Dict, Optional, List

from fastapi import Depends

from common.functional import BiFunction
from contracts.application.acme.dynamic.document_operation_result import DocumentOperationResult
from contracts.legacy.user import User
from contracts.legacy.user_repository import UserRepository
from contracts.model.content.document_number import DocumentNumber
from contracts.model.content_id import ContentId
from contracts.model.document_header import DocumentHeader
from contracts.model.document_header_repository import DocumentHeaderRepository
from contracts.model.state.dynamic.acme.acme_contract_state_assembler import AcmeContractStateAssembler
from contracts.model.state.dynamic.change_command import ChangeCommand
from contracts.model.state.dynamic.state import State
from contracts.model.state.dynamic.state_config import StateConfig


class DocumentResourceManager:
    document_header_repository: DocumentHeaderRepository
    assembler: AcmeContractStateAssembler
    user_repository: UserRepository

    def __init__(
            self,
            document_header_repository: DocumentHeaderRepository = Depends(DocumentHeaderRepository),
            assembler: AcmeContractStateAssembler = Depends(AcmeContractStateAssembler),
            user_repository: UserRepository = Depends(UserRepository),
     ):
        self.document_header_repository = document_header_repository
        self.assembler = assembler
        self.user_repository = user_repository

    def create_document(self, author_id: int) -> DocumentOperationResult:
        author: User = self.user_repository.get_one(author_id)

        number: DocumentNumber = self.generate_number()
        document_header: DocumentHeader = DocumentHeader(author.id, number)

        state_config: StateConfig = self.assembler.assemble()
        state: State = state_config.begin(document_header)

        self.document_header_repository.save(document_header)

        return self.generate_document_operation_result(DocumentOperationResult.Result.SUCCESS, state)

    def change_state(self, document_id: int, desired_state: str, params: Dict[str, object]) -> DocumentOperationResult:
        document_header: DocumentHeader = self.document_header_repository.get_one(document_id)
        state_config: StateConfig = self.assembler.assemble()
        state: State = state_config.recreate(document_header)

        state = state.change_state(ChangeCommand(desired_state, params))

        self.document_header_repository.save(document_header)

        return self.generate_document_operation_result(DocumentOperationResult.Result.SUCCESS, state)

    def change_content(self, header_id: int, content_version: ContentId) -> DocumentOperationResult:
        document_header: DocumentHeader = self.document_header_repository.get_one(header_id)
        state_config: StateConfig = self.assembler.assemble()
        state: State = state_config.recreate(document_header)
        state = state.change_content(content_version)

        self.document_header_repository.save(document_header)
        return self.generate_document_operation_result(DocumentOperationResult.Result.SUCCESS, state)

    def generate_document_operation_result(self, result: DocumentOperationResult.Result, state: State):
        return DocumentOperationResult(
            result,
            state.document_header.id,
            state.document_header.get_document_number(),
            state.state_descriptor,
            state.document_header.get_content_id(),
            self.extract_possible_transitions_and_rules(state),
            state.is_content_editable(),
            self.extract_content_change_predicate(state)
        )

    def extract_content_change_predicate(self, state: State) -> Optional[str]:
        if state.is_content_editable():
            return (
                f"{state.content_change_predicate.__class__.__module__}."
                f"{state.content_change_predicate.__class__.__name__}"
            )
        return None

    def extract_possible_transitions_and_rules(self, state: State) -> Dict[str, List[str]]:
        transitions_and_rules: Dict[str, List[str]] = {}

        state_change_predicates: Dict[State, List[BiFunction[State, ChangeCommand, bool]]] = \
            state.state_change_predicates
        for s in state_change_predicates:
            # transition to self is not important
            if s == state:
                continue

            predicates: List[BiFunction[State, ChangeCommand, bool]] = state_change_predicates.get(s)
            rule_names: List[str] = []
            for predicate in predicates:
                rule_names.append(predicate.__class__.__name__)
            transitions_and_rules[s.state_descriptor] = rule_names

        return transitions_and_rules

    def generate_number(self) -> DocumentNumber:
        return DocumentNumber(f"nr: {random.randint(0, sys.maxsize)}")  # TODO integrate with doc number generator
