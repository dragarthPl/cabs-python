from contracts.legacy.document_status import DocumentStatus


class UnsupportedTransitionException(Exception):
    current: DocumentStatus
    desired: DocumentStatus

    def __init__(self, current: DocumentStatus, desired: DocumentStatus):
        super().__init__(f"can not transit form {current} to {desired}")
        self.current = current
        self.desired = desired
