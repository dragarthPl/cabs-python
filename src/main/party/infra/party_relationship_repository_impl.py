from typing import Optional, List

from sqlalchemy import text
from fastapi import Depends
from sqlmodel import Session

from core.database import get_session

from party.api.party_id import PartyId
from party.model.party.party import Party
from party.model.party.party_relationship import PartyRelationship
from party.model.party.party_relationship_repository import PartyRelationshipRepository


class PartyRelationshipRepositoryImpl(PartyRelationshipRepository):

    def __init__(self, session: Session = Depends(get_session)):
        self.session = session

    def put(
        self,
        party_relationship: str,
        party_a_role: str,
        party_a: Party,
        party_b_role: str,
        party_b: Party,
    ) -> PartyRelationship:
        stmt = text(
            "SELECT * FROM PartyRelationship AS r "
            "WHERE r.name = :name "
            "AND ("
                "(r.party_a_id = :party_a AND r.party_b_id = :party_b) "
                "OR "
                "(r.party_a_id = :party_b AND r.party_b_id = :party_a)"
            ")"
        )
        stmt = stmt.bindparams(
            name=party_relationship,
            party_a=str(party_a.id),
            party_b=str(party_b.id),

        )
        parties = self.session.execute(stmt).all()

        relationship: PartyRelationship = None
        if parties:
            relationship = parties[0]
        else:
            relationship = PartyRelationship()
            self.session.add(relationship)
            self.session.commit()
            self.session.refresh(relationship)

        relationship.name = party_relationship
        relationship.party_a = party_a
        relationship.party_b = party_b
        relationship.role_a = party_a_role
        relationship.role_b = party_b_role

        self.session.add(relationship)
        self.session.commit()
        self.session.refresh(relationship)

        return relationship

    def find_relationship_for(self, party_id: PartyId, relationship_name: str) -> List[PartyRelationship]:
        stmt = text(
            "SELECT * FROM PartyRelationship AS r "
            "WHERE r.name = :name "
            "AND "
            "(r.party_a_id = :id OR r.party_b_id = :id)"
        )
        parties = self.session.query(PartyRelationship).from_statement(stmt).params(
            name=relationship_name,
            id=party_id.id.hex,
        ).all()

        if not parties:
            return []
        return [parties[0]]

