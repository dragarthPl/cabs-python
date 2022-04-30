from typing import Optional

from sqlalchemy import types
from sqlmodel import Field, SQLModel


class BaseEntity(SQLModel):

    id: Optional[int] = Field(default=None, primary_key=True)
    version: int = 1


class EnumAsInteger(types.TypeDecorator):
    """Column type for storing Python enums in a database INTEGER column.

    This will behave erratically if a database value does not correspond to
    a known enum value.
    """
    impl = types.Integer # underlying database type

    def __init__(self, enum_type):
        super(EnumAsInteger, self).__init__()
        self.enum_type = enum_type

    def process_bind_param(self, value, dialect):
        if isinstance(value, self.enum_type):
            return value.value
        raise ValueError('expected %s value, got %s'
            % (self.enum_type.__name__, value.__class__.__name__))

    def process_result_value(self, value, dialect):
        return self.enum_type(value)

    def copy(self, **kwargs):
        return EnumAsInteger(self.enum_type)