from party.model.party.party import Party
from party.model.role.party_based_role import PartyBasedRole


class Insured(PartyBasedRole):
    def __init__(self, party: Party):
        super().__init__(party)
