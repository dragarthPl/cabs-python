from unittest import TestCase

from contracts.application.acme.straigthforward.contract_result import ContractResult
from contracts.model.state.straightforward.base_state import BaseState


class ContractResultAssert(TestCase):
    __result: ContractResult

    def __init__(self, result: ContractResult):
        super().__init__()
        self.__result = result
        self.assertEqual(ContractResult.Result.SUCCESS, result.result)

    def state(self, state: BaseState) -> 'ContractResultAssert':
        self.assertEqual(state.get_state_descriptor(), self.__result.state_descriptor)
        return self
