from money import Money
from party.model.party.party import Party
from repair.api.repair_request import RepairRequest
from repair.model.roles.repair.repairing_result import RepairingResult
from repair.model.roles.repair.role_for_repairer import RoleForRepairer


class Warranty(RoleForRepairer):

    def __init__(self, party: Party):
        super().__init__(party)

    def handle(self, repair_request: RepairRequest) -> RepairingResult:
        handled_parts = set(repair_request.parts_to_repair)

        return RepairingResult(self.party.id, Money.ZERO, handled_parts)
