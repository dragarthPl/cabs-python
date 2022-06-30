from unittest import TestCase

from contracts.application.acme.dynamic.document_operation_result import DocumentOperationResult
from contracts.model.content_id import ContentId


class DocumentOperationResultAssert(TestCase):
    __result: DocumentOperationResult

    def __init__(self, result: DocumentOperationResult):
        super().__init__()
        self.__result = result

    def editable(self):
        self.assertTrue(self.__result.is_content_change_possible())
        return self

    def uneditable(self) -> 'DocumentOperationResultAssert':
        self.assertFalse(self.__result.is_content_change_possible())
        return self

    def state(self, state: str) -> 'DocumentOperationResultAssert':
        self.assertEqual(state, self.__result.state_name)
        return self

    def content(self, content_id: ContentId) -> 'DocumentOperationResultAssert':
        self.assertEqual(content_id, self.__result.content_id)
        return self

    def possibleNextStates(self, *states: str) -> 'DocumentOperationResultAssert':
        self.assertEqual(
            set(states),
            self.__result.possible_transitions_and_rules.keys()
        )
        return self
