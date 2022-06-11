import abc

from party.model.party.party import Party
from party.model.role.party_based_role import PartyBasedRole
from repair.api.assistance_request import AssistanceRequest


class RoleForAssistance(PartyBasedRole, metaclass=abc.ABCMeta):
    def __init__(self, party: Party):
        super().__init__(party)

    def handle(self, request: AssistanceRequest):
        raise NotImplementedError
