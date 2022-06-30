import uuid
from unittest import TestCase

from common.base_entity import new_uuid
from contracts.model.content.document_number import DocumentNumber
from contracts.model.content_id import ContentId
from contracts.model.document_header import DocumentHeader
from contracts.model.state.straightforward.acme.draft_state import DraftState
from contracts.model.state.straightforward.acme.published_state import PublishedState
from contracts.model.state.straightforward.acme.verified_state import VerifiedState
from contracts.model.state.straightforward.base_state import BaseState


class TestAcmeContract(TestCase):
    ANY_NUMBER: DocumentNumber = DocumentNumber("nr: 1")
    ANY_USER: int = 1
    OTHER_USER: int = 2
    ANY_VERSION: ContentId = ContentId(new_uuid())
    OTHER_VERSION: ContentId = ContentId((new_uuid()))

    state: BaseState

    def test_only_draft_can_be_verified_by_user_other_than_creator(self):
        # given
        state = self.__draft().change_content(self.ANY_VERSION)
        # when
        state = state.change_state(VerifiedState(self.OTHER_USER))
        # then
        self.assertEqual(VerifiedState, state.__class__)
        self.assertEqual(self.OTHER_USER, state.document_header.get_verifier())

    def test_can_not_change_published(self):
        # given
        state = self.__draft().change_content(
            self.ANY_VERSION
        ).change_state(
            VerifiedState(self.OTHER_USER)
        ).change_state(PublishedState())
        # when
        state = state.change_content(self.OTHER_VERSION)
        # then
        self.assertEqual(PublishedState, state.__class__)
        self.assertEqual(self.ANY_VERSION, state.document_header.get_content_id())

    def test_changing_verified_moves_to_draft(self):
        # given
        state = self.__draft().change_content(self.ANY_VERSION)
        # when
        state = state.change_state(VerifiedState(self.OTHER_USER)).change_content(self.OTHER_VERSION)
        # then
        self.assertEqual(DraftState, state.__class__)
        self.assertEqual(self.OTHER_VERSION, state.document_header.get_content_id())

    def __draft(self) -> BaseState:
        header: DocumentHeader = DocumentHeader(self.ANY_USER, self.ANY_NUMBER)

        state: BaseState = DraftState()
        state.init(header)

        return state
