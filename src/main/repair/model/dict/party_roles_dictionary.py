import enum

from repair.model.roles.empty.customer import Customer
from repair.model.roles.empty.insured import Insured
from repair.model.roles.repair.extended_insurance import ExtendedInsurance
from repair.model.roles.repair.warranty import Warranty


class PartyRolesDictionary(enum.Enum):
    INSURER = ExtendedInsurance
    INSURED = Insured
    GUARANTOR = Warranty
    CUSTOMER = Customer

    @property
    def role_name(self) -> str:
        return self.__name

    def __init__(self, clazz):
        self.__name = f"{clazz.__module__}.{clazz.__name__}"

    def get_role_name(self):
        return self.role_name
