from common.functional import BiFunction
from contracts.model.document_header import DocumentHeader
from contracts.model.state.dynamic.change_command import ChangeCommand


class ChangeVerifier(BiFunction[DocumentHeader, ChangeCommand, None]):
    PARAM_VERIFIER: str = "verifier"

    def apply(self, document_header: DocumentHeader, command: ChangeCommand) -> None:
        document_header.verifier_id = command.get_param(self.PARAM_VERIFIER, int)
