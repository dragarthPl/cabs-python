from typing import Optional

from sqlmodel import Field, SQLModel


class BaseEntity(SQLModel):

    id: Optional[int] = Field(default=None, primary_key=True)
    version: int = 1


