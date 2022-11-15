import uuid
from unittest import TestCase

from common.base_entity import new_uuid
from contracts.model.content.document_number import DocumentNumber
from contracts.model.content_id import ContentId
from contracts.model.document_header import DocumentHeader
from contracts.model.state.dynamic.acme.acme_contract_state_assembler import AcmeContractStateAssembler
from contracts.model.state.dynamic.change_command import ChangeCommand
from contracts.model.state.dynamic.config.events.document_published import DocumentPublished
from contracts.model.state.dynamic.state import State
from contracts.model.state.dynamic.state_config import StateConfig
from tests.contracts.model.state.dynamic.fake_document_publisher import FakeDocumentPublisher


class TestAcmeContract(TestCase):
    ANY_NUMBER: DocumentNumber = DocumentNumber("nr: 1")
    ANY_USER: int = 1
    OTHER_USER: int = 2
    ANY_VERSION: ContentId = ContentId(new_uuid())
    OTHER_VERSION: ContentId = ContentId((new_uuid()))

    publisher: FakeDocumentPublisher

    def draft(self) -> State:

        header: DocumentHeader = DocumentHeader(self.ANY_USER, self.ANY_NUMBER)
        header.state_descriptor = AcmeContractStateAssembler.DRAFT
        self.publisher = FakeDocumentPublisher()

        assembler: AcmeContractStateAssembler = AcmeContractStateAssembler(self.publisher)
        config: StateConfig = assembler.assemble()
        state: State = config.recreate(header)

        return state

    def test_draft_can_be_verified_by_user_other_than_creator(self):
        # given
        state: State = self.draft().change_content(self.ANY_VERSION)
        # when
        state = state.change_state(
            ChangeCommand(
                AcmeContractStateAssembler.VERIFIED
            ).with_param(
                AcmeContractStateAssembler.PARAM_VERIFIER,
                self.OTHER_USER
            )
        )
        # then
        self.assertEqual(AcmeContractStateAssembler.VERIFIED, state.state_descriptor)
        self.assertEqual(self.OTHER_USER, state.document_header.get_verifier())

    def test_can_not_change_published(self):
        # given
        state: State = self.draft().change_content(
            self.ANY_VERSION
        ).change_state(
            ChangeCommand(
                AcmeContractStateAssembler.VERIFIED
            ).with_param(
                AcmeContractStateAssembler.PARAM_VERIFIER,
                self.OTHER_USER
            )
        ).change_state(
            ChangeCommand(AcmeContractStateAssembler.PUBLISHED)
        )

        self.publisher.contains(DocumentPublished)
        self.publisher.reset()
        # when
        self.publisher.no_events()
        # then
        self.assertEqual(AcmeContractStateAssembler.PUBLISHED, state.state_descriptor)
        self.assertEqual(self.ANY_VERSION, state.document_header.get_content_id())

    def test_changing_verified_moves_to_draft(self):
        # given
        state: State = self.draft().change_content(
            self.ANY_VERSION
        ).change_state(
            ChangeCommand(
                AcmeContractStateAssembler.VERIFIED
            ).with_param(
                AcmeContractStateAssembler.PARAM_VERIFIER,
                self.OTHER_USER
            )
        )
        # when
        state = state.change_content(self.OTHER_VERSION)
        # then
        self.assertEqual(AcmeContractStateAssembler.DRAFT, state.state_descriptor)
        self.assertEqual(self.OTHER_VERSION, state.document_header.get_content_id())

    def test_can_change_state_to_the_same(self):
        state: State = self.draft().change_content(
            self.ANY_VERSION
        )

        self.assertEqual(AcmeContractStateAssembler.DRAFT, state.state_descriptor)
        state.change_state(ChangeCommand(AcmeContractStateAssembler.DRAFT))
        self.assertEqual(AcmeContractStateAssembler.DRAFT, state.state_descriptor)

        state = state.change_state(
            ChangeCommand(
                AcmeContractStateAssembler.VERIFIED
            ).with_param(
                AcmeContractStateAssembler.PARAM_VERIFIER,
                self.OTHER_USER
            )
        )
        self.assertEqual(AcmeContractStateAssembler.VERIFIED, state.state_descriptor)
        state = state.change_state(
            ChangeCommand(
                AcmeContractStateAssembler.VERIFIED
            ).with_param(
                AcmeContractStateAssembler.PARAM_VERIFIER,
                self.OTHER_USER
            )
        )
        self.assertEqual(AcmeContractStateAssembler.VERIFIED, state.state_descriptor)

        state = state.change_state(ChangeCommand(AcmeContractStateAssembler.PUBLISHED))
        self.assertEqual(AcmeContractStateAssembler.PUBLISHED, state.state_descriptor)
        state = state.change_state(ChangeCommand(AcmeContractStateAssembler.PUBLISHED))
        self.assertEqual(AcmeContractStateAssembler.PUBLISHED, state.state_descriptor)

        state = state.change_state(ChangeCommand(AcmeContractStateAssembler.ARCHIVED))
        self.assertEqual(AcmeContractStateAssembler.ARCHIVED, state.state_descriptor)
        state = state.change_state(ChangeCommand(AcmeContractStateAssembler.ARCHIVED))
        self.assertEqual(AcmeContractStateAssembler.ARCHIVED, state.state_descriptor)
