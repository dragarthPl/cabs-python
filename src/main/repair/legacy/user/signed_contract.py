from typing import Set

from sqlalchemy import Column, JSON
from sqlmodel import Field

from common.base_entity import BaseEntity
from repair.legacy.parts.parts import Parts


class SignedContract(BaseEntity, table=True):
    __table_args__ = {'extend_existing': True}

    # @ElementCollection(fetch = FetchType.EAGER)
    covered_parts: Set[Parts] = Field(default={}, sa_column=Column(JSON))
    coverage_ratio: float
