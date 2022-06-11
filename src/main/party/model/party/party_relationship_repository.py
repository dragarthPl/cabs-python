import abc
from typing import Optional

from party.api.party_id import PartyId
from party.model.party.party import Party
from party.model.party.party_relationship import PartyRelationship


class PartyRelationshipRepository(metaclass=abc.ABCMeta):
    def put(
        self,
        party_relationship: str,
        party_a_role: str,
        party_a: Party,
        party_b_role: str,
        party_b: Party,
    ) -> PartyRelationship:
        raise NotImplementedError

    def find_relationship_for(self, party_id: PartyId, relationship_name: str) -> Optional[PartyRelationship]:
        raise NotImplementedError
