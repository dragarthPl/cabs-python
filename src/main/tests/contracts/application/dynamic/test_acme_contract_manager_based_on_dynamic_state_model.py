from typing import Dict, Any
from unittest import TestCase

import fastapi
from fastapi.params import Depends

from common.application_event_publisher import ApplicationEventPublisher
from contracts.application.editor.commit_result import CommitResult
from contracts.application.editor.document_dto import DocumentDTO
from contracts.model.state.dynamic.config.statechange.author_is_not_averifier import AuthorIsNotAVerifier
from core.database import create_db_and_tables, drop_db_and_tables

from contracts.application.acme.dynamic.document_operation_result import DocumentOperationResult
from contracts.application.acme.dynamic.document_resource_manager import DocumentResourceManager
from contracts.application.editor.document_editor import DocumentEditor
from contracts.legacy.user import User
from contracts.legacy.user_repository import UserRepository
from contracts.model.content.content_version import ContentVersion
from contracts.model.content.document_number import DocumentNumber
from contracts.model.content_id import ContentId
from contracts.model.state.dynamic.acme.acme_contract_state_assembler import AcmeContractStateAssembler

from tests.contracts.application.dynamic.document_operation_result_assert import DocumentOperationResultAssert
from tests.common.fixtures import DependencyResolver
from tests.contracts.application.straightforward.acme.test_acme_contract_process_based_on_straightforward_state_model import \
    DefaultFakeApplicationEventPublisher

dependency_resolver = DependencyResolver(abstract_map={
    "Depends(ApplicationEventPublisher)": fastapi.Depends(DefaultFakeApplicationEventPublisher)
})


class TestAcmeContractManagerBasedOnDynamicStateModel(TestCase):
    editor: DocumentEditor = dependency_resolver.resolve_dependency(Depends(DocumentEditor))
    document_resource_manager: DocumentResourceManager = dependency_resolver.resolve_dependency(
        Depends(DocumentResourceManager)
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
        result: DocumentOperationResult = self.document_resource_manager.change_content(self.header_id, content_id)
        DocumentOperationResultAssert(
            result
        ).state(
            AcmeContractStateAssembler.DRAFT
        ).editable().possibleNextStates(
            AcmeContractStateAssembler.VERIFIED,
            AcmeContractStateAssembler.ARCHIVED
        )
        # when
        result = self.document_resource_manager.change_state(
            self.header_id,
            AcmeContractStateAssembler.VERIFIED,
            self.verifier_param()
        )
        # then
        DocumentOperationResultAssert(
            result
        ).state(
            AcmeContractStateAssembler.VERIFIED
        ).editable().possibleNextStates(
            AcmeContractStateAssembler.PUBLISHED,
            AcmeContractStateAssembler.ARCHIVED
        )

    def test_author_can_not_verify(self):
        # given
        self.crate_acme_contract(self.author)
        content_id: ContentId = self.commit_content(self.CONTENT_1)
        result: DocumentOperationResult = self.document_resource_manager.change_content(self.header_id, content_id)
        DocumentOperationResultAssert(result).state(AcmeContractStateAssembler.DRAFT)
        # when
        result = self.document_resource_manager.change_state(
            self.header_id,
            AcmeContractStateAssembler.VERIFIED,
            self.author_param()
        )
        # then
        DocumentOperationResultAssert(result).state(AcmeContractStateAssembler.DRAFT)

    def test_changing_content_of_verified_moves_back_to_draft(self):
        # given
        self.crate_acme_contract(self.author)
        content_id: ContentId = self.commit_content(self.CONTENT_1)
        result: DocumentOperationResult = self.document_resource_manager.change_content(self.header_id, content_id)
        DocumentOperationResultAssert(result).state(AcmeContractStateAssembler.DRAFT).editable()

        result = self.document_resource_manager.change_state(
            self.header_id,
            AcmeContractStateAssembler.VERIFIED,
            self.verifier_param()
        )
        DocumentOperationResultAssert(result).state(AcmeContractStateAssembler.VERIFIED).editable()
        # when
        content_id: ContentId = self.commit_content(self.CONTENT_2)
        result = self.document_resource_manager.change_content(self.header_id, content_id)
        # then
        DocumentOperationResultAssert(result).state(AcmeContractStateAssembler.DRAFT).editable()

    def test_published_can_not_be_changed(self):
        # given
        self.crate_acme_contract(self.author)
        first_content_id: ContentId = self.commit_content(self.CONTENT_1)
        result: DocumentOperationResult = self.document_resource_manager.change_content(
            self.header_id,
            first_content_id
        )
        DocumentOperationResultAssert(result).state(AcmeContractStateAssembler.DRAFT).editable()

        result = self.document_resource_manager.change_state(
            self.header_id,
            AcmeContractStateAssembler.VERIFIED,
            self.verifier_param()
        )
        DocumentOperationResultAssert(result).state(AcmeContractStateAssembler.VERIFIED).editable()

        result = self.document_resource_manager.change_state(
            self.header_id,
            AcmeContractStateAssembler.PUBLISHED,
            self.empty_param()
        )
        DocumentOperationResultAssert(result).state(AcmeContractStateAssembler.PUBLISHED).uneditable()
        # when
        new_content_id: ContentId = self.commit_content(self.CONTENT_2)
        result = self.document_resource_manager.change_content(self.header_id, new_content_id)
        # then
        DocumentOperationResultAssert(
            result
        ).state(
            AcmeContractStateAssembler.PUBLISHED
        ).uneditable(

        ).content(
            first_content_id
        )

    def crate_acme_contract(self, user: User):
        result: DocumentOperationResult = self.document_resource_manager.create_document(user.id)
        self.document_number = result.document_number
        self.header_id = result.document_header_id

    def commit_content(self, content: str) -> ContentId:

        doc: DocumentDTO = DocumentDTO(None, content, self.ANY_VERSION)

        result: CommitResult = self.editor.commit(doc)
        self.assertEqual(CommitResult.Result.SUCCESS, result.result)
        return ContentId(result.content_id)

    def verifier_param(self) -> Dict[str, object]:
        return dict([(AuthorIsNotAVerifier.PARAM_VERIFIER, self.verifier.id)])

    def author_param(self) -> Dict[str, object]:
        return dict([(AuthorIsNotAVerifier.PARAM_VERIFIER, self.author.id)])

    def empty_param(self) -> Dict[str, object]:
        return {}

    def tearDown(self) -> None:
        drop_db_and_tables()
