import abc

from party.model.party.party import Party
from party.model.role.party_based_role import PartyBasedRole
from repair.api.repair_request import RepairRequest


class RoleForRepairer(PartyBasedRole, metaclass=abc.ABCMeta):

    def __init__(self, party: Party):
        super().__init__(party)

    def handle(self, repair_request: RepairRequest):
        raise NotImplementedError
