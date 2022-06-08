import enum
from typing import Dict


class JobResult:
    class Decision(enum.Enum):
        REDIRECTION = 1
        ACCEPTED = 2
        ERROR = 3

    decision: Decision
    params: Dict[str, object]

    def __init__(self, decision: Decision):
        self.params = {}
        self.decision = decision

    def add_param(self, name: str, value: object):
        self.params[name] = value
        return self
