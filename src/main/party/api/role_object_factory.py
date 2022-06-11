from typing import Type, Dict

from party.model.party.party import Party
from party.model.party.party_relationship import PartyRelationship
from party.model.role.party_based_role import PartyBasedRole


class RoleObjectFactory:

    roles = Dict[str, PartyBasedRole]

    def __init__(self):
        self.roles = {}

    def has_role(self, role):
        return role in self.roles

    @classmethod
    def from_relationship(cls, party_relationship: PartyRelationship) -> 'RoleObjectFactory':
        role_object: 'RoleObjectFactory' = cls()
        role_object.add(party_relationship)
        return role_object

    def add(self, party_relationship: PartyRelationship) -> None:
        self.add_role(party_relationship.role_a, party_relationship.party_a)
        self.add_role(party_relationship.role_b, party_relationship.party_b)

    @staticmethod
    def format_class_key(clazz):
        return f"{clazz.__module__}.{clazz.__name__}"

    def add_role(self, role: str, party: Party):
        try:
            # in sake of simplicity: a role name is same as a class name with no mapping between them
            class_full_path = role.split(".")
            cast_class = __import__(class_full_path[0])
            for elem in class_full_path[1:]:
                cast_class = getattr(cast_class, elem)

            clazz: Type[PartyBasedRole] = cast_class
            instance: PartyBasedRole = clazz(party)

            parent_class = clazz.__base__
            key = self.format_class_key(parent_class) if parent_class != PartyBasedRole else role
            self.roles[key] = instance
        except Exception as e:
            raise AttributeError(e)

    def get_role(self, role):
        return self.roles.get(self.format_class_key(role))
