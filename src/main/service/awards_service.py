import abc
import sys
from datetime import datetime
from functools import reduce
from typing import Callable

from config.app_properties import AppProperties, get_app_properties
from dateutil.relativedelta import relativedelta
from dto.awards_account_dto import AwardsAccountDTO
from entity import Client, ConstantUntil
from entity.miles.awarded_miles import AwardedMiles
from entity.miles.awards_account import AwardsAccount
from fastapi import Depends
from repository.awards_account_repository import AwardsAccountRepositoryImp
from repository.client_repository import ClientRepositoryImp
from repository.transit_repository import TransitRepositoryImp


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


class AwardsServiceImpl(AwardsService):
    account_repository: AwardsAccountRepositoryImp
    client_repository: ClientRepositoryImp
    transit_repository: TransitRepositoryImp
    app_properties: AppProperties

    def __init__(
            self,
            account_repository: AwardsAccountRepositoryImp = Depends(AwardsAccountRepositoryImp),
            client_repository: ClientRepositoryImp = Depends(ClientRepositoryImp),
            transit_repository: TransitRepositoryImp = Depends(TransitRepositoryImp),
            app_properties: AppProperties = Depends(get_app_properties)
    ):
        self.account_repository = account_repository
        self.client_repository = client_repository
        self.transit_repository = transit_repository
        self.app_properties = app_properties

    def find_by(self, client_id: int) -> AwardsAccountDTO:
        return AwardsAccountDTO(
            awards_account=self.account_repository.find_by_client(self.client_repository.get_one(client_id))
        )

    def register_to_program(self, client_id: int) -> None:
        client = self.client_repository.get_one(client_id)

        if client is None:
            raise AttributeError("Client does not exists, id = " + str(client_id))

        account = AwardsAccount.not_active_account(client, datetime.now())
        self.account_repository.save(account)

    def activate_account(self, client_id: int) -> None:
        account = self.account_repository.find_by_client(self.client_repository.get_one(client_id))

        if account is None:
            raise AttributeError("Account does not exists, client_id = " + str(client_id))

        account.activate()
        self.account_repository.save(account)

    def deactivate_account(self, client_id: int) -> None:
        account = self.account_repository.find_by_client(self.client_repository.get_one(client_id))

        if account is None:
            raise AttributeError("Account does not exists, client_id = " + str(client_id))

        account.deactivate()
        self.account_repository.save(account)

    def register_miles(self, client_id: int, transit_id: int) -> AwardedMiles:
        account = self.account_repository.find_by_client(self.client_repository.get_one(client_id))
        transit = self.transit_repository.get_one(transit_id)
        if transit is None:
            raise AttributeError("Transit does not exists, id = " + str(transit_id))

        if account == None or not account.is_active:
            return None
        else:
            expire_at = datetime.now() + relativedelta(days=self.app_properties.miles_expiration_in_days)
            miles = account.add_expiring_miles(
                self.app_properties.default_miles_bonus,
                expire_at,
                transit,
                datetime.now()
            )
            self.account_repository.save(account)
            return miles

    def is_sunday(self):
        return datetime.now().weekday() == 6

    def register_non_expiring_miles(self, client_id: int, miles: int) -> AwardedMiles:
        account = self.account_repository.find_by_client(self.client_repository.get_one(client_id))

        if account == None:
            raise AttributeError("Account does not exists, client_id = " + str(client_id))
        else:
            _miles = account.add_non_expiring_miles(
                miles,
                datetime.now()
            )
            self.account_repository.save(account)
            return _miles

    def remove_miles(self, client_id: int, miles: int) -> None:
        client = self.client_repository.get_one(client_id)
        account = self.account_repository.find_by_client(client)

        if account is None:
            raise AttributeError("Account does not exists, client_id = " + str(client_id))
        else:
            account.remove(
                miles,
                datetime.now(),
                self.choose_strategy(
                    len(self.transit_repository.find_by_client(client)),
                    len(client.claims),
                    client.type,
                    self.is_sunday()
                )
            )

    def choose_strategy(
            self, transits_counter: int, claims_counter: int, client_type: Client.Type, is_sunday: bool) -> Callable:
        if claims_counter >= 3:
            return lambda x: (x is None, -x.get_expiration_date().timestamp() or -sys.maxsize)
        elif client_type == Client.Type.VIP:
            return lambda x: (x.can_expire(), x.get_expiration_date() or datetime.min)
        elif transits_counter >= 15 and is_sunday:
            return lambda x: (x.can_expire(), x.get_expiration_date() or datetime.min)
        elif transits_counter >= 15:
            return lambda x: (x.can_expire(), x.date)
        else:
            return lambda x: x.date

    def calculate_balance(self, client_id: int) -> int:
        client = self.client_repository.get_one(client_id)
        account = self.account_repository.find_by_client(client)

        return account.calculate_balance(datetime.now())

    def transfer_miles(self, from_client_id: int, to_client_id: int, miles):
        from_client = self.client_repository.get_one(from_client_id)
        account_from = self.account_repository.find_by_client(from_client)
        account_to = self.account_repository.find_by_client(self.client_repository.get_one(to_client_id))
        now: datetime = datetime.now()

        if account_from is None:
            raise AttributeError("Account does not exists, id = " + str(from_client_id))
        if account_to is None:
            raise AttributeError("Account does not exists, id = " + str(to_client_id))

        account_from.move_miles_to(account_to, miles, now)
        self.account_repository.save(account_from)
        self.account_repository.save(account_to)
