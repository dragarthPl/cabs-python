import uuid as uuid_pkg

from sqlmodel import Field, SQLModel

from common.base_entity import new_uuid


class PartyRole(SQLModel, table=True):
    __table_args__ = {'extend_existing': True}

    id: uuid_pkg.UUID = Field(
        default_factory=new_uuid,
        nullable=False,
        primary_key=True
    )

    name: str
