import abc
from loyalty.awards_account_dto import AwardsAccountDTO
from loyalty.awarded_miles import AwardedMiles


class AwardsService(metaclass=abc.ABCMeta):

    def find_by(self, client_id: int) -> AwardsAccountDTO:
        raise NotImplementedError

    def register_to_program(self, client_id: int) -> None:
        raise NotImplementedError

    def activate_account(self, client_id: int) -> None:
        raise NotImplementedError

    def deactivate_account(self, client_id: int) -> None:
        raise NotImplementedError

    def register_miles(self, client_id: int, transit_id: int) -> AwardedMiles:
        raise NotImplementedError

    def register_non_expiring_miles(self, client_id: int, miles: int) -> AwardedMiles:
        raise NotImplementedError

    def remove_miles(self, client_id: int, miles: int) -> None:
        raise NotImplementedError

    def calculate_balance(self, client_id: int) -> int:
        raise NotImplementedError

    def transfer_miles(self, from_client_id: int, to_client_id: int, miles: int) -> None:
        raise NotImplementedError
