import sys
import random

from fastapi import Depends

from contracts.application.acme.straigthforward.acme_state_factory import AcmeStateFactory
from contracts.application.acme.straigthforward.contract_result import ContractResult
from contracts.legacy.user import User
from contracts.legacy.user_repository import UserRepository
from contracts.model.content.document_number import DocumentNumber
from contracts.model.content_id import ContentId
from contracts.model.document_header import DocumentHeader
from contracts.model.document_header_repository import DocumentHeaderRepository
from contracts.model.state.straightforward.acme.verified_state import VerifiedState
from contracts.model.state.straightforward.base_state import BaseState


class AcmeContractProcessBasedOnStraightforwardDocumentModel:
    user_repository: UserRepository

    document_header_repository: DocumentHeaderRepository

    state_factory: AcmeStateFactory

    def __init__(
            self,
            user_repository: UserRepository = Depends(UserRepository),
            document_header_repository: DocumentHeaderRepository = Depends(DocumentHeaderRepository),
            state_factory: AcmeStateFactory = Depends(AcmeStateFactory),
    ):
        self.user_repository = user_repository
        self.document_header_repository = document_header_repository
        self.state_factory = state_factory

    def create_contract(self, author_id: int) -> ContractResult:
        author: User = self.user_repository.get_one(author_id)

        number: DocumentNumber = self.generate_number()
        header: DocumentHeader = DocumentHeader(author.id, number)

        self.document_header_repository.save(header)

        return ContractResult(
            ContractResult.Result.SUCCESS,
            header.id,
            number,
            header.state_descriptor
        )

    def verify(self, header_id, verifier_id: int):
        verifier: User = self.user_repository.get_one(verifier_id)
        # TODO user authorization

        header: DocumentHeader = self.document_header_repository.get_one(header_id)

        state: BaseState = self.state_factory.create(header)
        state = state.change_state(VerifiedState(verifier_id))

        self.document_header_repository.save(header)
        return ContractResult(
            ContractResult.Result.SUCCESS,
            header_id,
            header.get_document_number(),
            header.state_descriptor
        )

    def change_content(self, header_id: int, content_version: ContentId):
        header: DocumentHeader = self.document_header_repository.get_one(header_id)

        state: BaseState = self.state_factory.create(header)
        state = state.change_content(content_version)

        self.document_header_repository.save(header)
        return ContractResult(
            ContractResult.Result.SUCCESS,
            header_id,
            header.get_document_number(),
            header.state_descriptor
        )

    def generate_number(self) -> DocumentNumber:
        return DocumentNumber(f"nr: {random.randint(0, sys.maxsize)}")  # TODO integrate with doc number generator
