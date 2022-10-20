from typing import Optional

from injector import inject

from party.api.party_id import PartyId
from party.infra.party_relationship_repository_impl import PartyRelationshipRepositoryImpl
from party.model.party.party_relationship import PartyRelationship
from party.model.party.party_relationship_repository import PartyRelationshipRepository


class PartyMapper:
    party_relationship_repository: PartyRelationshipRepository

    @inject
    def __init__(
        self,
        party_relationship_repository: PartyRelationshipRepository,
    ):
        self.party_relationship_repository = party_relationship_repository

    def map_relation(self, party_id: PartyId, relationship_name: str) -> Optional[PartyRelationship]:
        return self.party_relationship_repository.find_relationship_for(party_id, relationship_name)
