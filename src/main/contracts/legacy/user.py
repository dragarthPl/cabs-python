from common.base_entity import BaseEntity


class User(BaseEntity, table=True):
    __table_args__ = {'extend_existing': True}

    def __eq__(self, other):
        if not isinstance(other, User):
            return False
        return self.id == other.id
