import uuid as uuid_pkg
from uuid import UUID, uuid4
from typing import Optional

from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from sqlmodel import Field, SQLModel, Relationship

from party.model.party.party import Party


class PartyRelationship(SQLModel, table=True):
    __table_args__ = {'extend_existing': True}

    id: UUID = Field(
        default_factory=uuid4,
        nullable=False,
        primary_key=True
    )

    name: Optional[str]
    role_a: Optional[str]
    role_b: Optional[str]

    # @ManyToOne
    party_a_id: Optional[uuid_pkg.UUID] = Field(default=None, foreign_key="party.id")
    party_a: Optional[Party] = Relationship(
        sa_relationship_kwargs=dict(foreign_keys="[PartyRelationship.party_a_id]")
    )

    # @ManyToOne
    party_b_id: Optional[uuid_pkg.UUID] = Field(default=None, foreign_key="party.id")
    party_b: Optional[Party] = Relationship(
        sa_relationship_kwargs=dict(foreign_keys="[PartyRelationship.party_b_id]")
    )

