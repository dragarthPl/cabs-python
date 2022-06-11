import abc

from party.model.party.party import Party


class PartyBasedRole(metaclass=abc.ABCMeta):
    party: Party

    def __init__(self, party: Party):
        self.party = party
