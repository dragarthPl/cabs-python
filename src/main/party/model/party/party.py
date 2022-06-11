import uuid as uuid_pkg

from sqlmodel import Field, SQLModel


class Party(SQLModel, table=True):
    __table_args__ = {'extend_existing': True}

    id: uuid_pkg.UUID = Field(
        default_factory=uuid_pkg.uuid4,
        nullable=False,
        primary_key=True
    )
