from repair.legacy.parts.parts import Parts
from repair.legacy.user.common_base_abstract_user import CommonBaseAbstractUser
from repair.legacy.user.employee_driver_with_own_car import EmployeeDriverWithOwnCar
from repair.legacy.user.signed_contract import SignedContract


class UserDAO:
    def get_one(self, user_id: int) -> CommonBaseAbstractUser:
        contract: SignedContract = SignedContract()
        contract.covered_parts = set(Parts)
        contract.coverage_ratio = 100.0

        user: EmployeeDriverWithOwnCar = EmployeeDriverWithOwnCar()
        user.contract = contract
        return user
