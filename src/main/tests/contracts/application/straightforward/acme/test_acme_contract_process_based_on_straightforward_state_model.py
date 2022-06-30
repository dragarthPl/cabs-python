from typing import Any
from unittest import TestCase

import fastapi
from fastapi.params import Depends

from common.application_event_publisher import ApplicationEventPublisher
from contracts.application.acme.straigthforward.acme_contract_process_based_on_straightforward_document_model import \
    AcmeContractProcessBasedOnStraightforwardDocumentModel
from contracts.application.acme.straigthforward.contract_result import ContractResult
from contracts.application.editor.commit_result import CommitResult
from contracts.application.editor.document_dto import DocumentDTO
from contracts.application.editor.document_editor import DocumentEditor
from contracts.legacy.user import User
from contracts.legacy.user_repository import UserRepository
from contracts.model.content.content_version import ContentVersion
from contracts.model.content.document_number import DocumentNumber
from contracts.model.content_id import ContentId
from contracts.model.state.straightforward.acme.verified_state import VerifiedState
from core.database import create_db_and_tables, drop_db_and_tables
from tests.common.fixtures import DependencyResolver
from tests.contracts.application.straightforward.acme.contract_result_assert import ContractResultAssert


class DefaultFakeApplicationEventPublisher(ApplicationEventPublisher):

    def __init__(self):
        ...

    def publish_event_object(self, event: Any):
        ...


dependency_resolver = DependencyResolver(abstract_map={
    "Depends(ApplicationEventPublisher)": fastapi.Depends(DefaultFakeApplicationEventPublisher)
})


class TestAcmeContractProcessBasedOnStraightforwardStateModel(TestCase):
    editor: DocumentEditor = dependency_resolver.resolve_dependency(Depends(DocumentEditor))
    contract_process: AcmeContractProcessBasedOnStraightforwardDocumentModel = dependency_resolver.resolve_dependency(
        Depends(AcmeContractProcessBasedOnStraightforwardDocumentModel)
    )
    user_repository: UserRepository = dependency_resolver.resolve_dependency(Depends(UserRepository))

    CONTENT_1: str = "content 1"
    CONTENT_2: str = "content 2"
    ANY_VERSION: ContentVersion = ContentVersion("v1")

    author: User
    verifier: User

    document_number: DocumentNumber
    header_id: int

    def setUp(self):
        create_db_and_tables()
        self.author = self.user_repository.save(User())
        self.verifier = self.user_repository.save(User())

    def test_verifier_other_than_author_can_verify(self):
        # given
        self.crate_acme_contract(self.author)
        content_id: ContentId = self.commit_content(self.CONTENT_1)
        self.contract_process.change_content(self.header_id, content_id)
        # when
        result: ContractResult = self.contract_process.verify(self.header_id, self.verifier.id)
        # then
        ContractResultAssert(result).state(VerifiedState(self.verifier.id))

    def commit_content(self, content: str) -> ContentId:
        doc: DocumentDTO = DocumentDTO(None, content, self.ANY_VERSION)
        result: CommitResult = self.editor.commit(doc)
        self.assertEquals(CommitResult.Result.SUCCESS, result.result)
        return ContentId(result.content_id)

    def crate_acme_contract(self, user: User):
        contract_result: ContractResult = self.contract_process.create_contract(user.id)
        self.document_number = contract_result.document_number
        self.header_id = contract_result.document_header_id

    def tearDown(self) -> None:
        drop_db_and_tables()
