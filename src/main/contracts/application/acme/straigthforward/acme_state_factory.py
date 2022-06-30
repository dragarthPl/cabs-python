from contracts.model.document_header import DocumentHeader
from contracts.model.state.straightforward.acme.draft_state import DraftState
from contracts.model.state.straightforward.base_state import BaseState


class AcmeStateFactory:
    @staticmethod
    def format_class_key(clazz):
        return f"{clazz.__module__}.{clazz.__name__}"

    def create(self, header: DocumentHeader) -> BaseState:
        # sample impl is based on class names
        # other possibilities: names Dependency Injection Containers, states persisted via ORM Discriminator mechanism,
        # mapper
        class_name: str = header.state_descriptor

        if not class_name:
            state: DraftState = DraftState()
            state.init(header)
            return state

        class_full_path = class_name.split(".")
        cast_class = __import__(class_full_path[0])
        for elem in class_full_path[1:]:
            cast_class = getattr(cast_class, elem)

        try:
            state: BaseState = cast_class()
            state.init(header)
            return state
        except Exception as e:
            raise e
