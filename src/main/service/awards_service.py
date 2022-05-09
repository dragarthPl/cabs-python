import abc
from datetime import datetime
from functools import reduce

from config.app_properties import AppProperties, get_app_properties
from dateutil.relativedelta import relativedelta
from dto.awards_account_dto import AwardsAccountDTO
from entity import Client, ConstantUntil
from entity.miles.awarded_miles import AwardedMiles
from entity.miles.awards_account import AwardsAccount
from fastapi import Depends
from repository.awarded_miles_repository import AwardedMilesRepositoryImp
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
    miles_repository: AwardedMilesRepositoryImp
    client_repository: ClientRepositoryImp
    transit_repository: TransitRepositoryImp
    app_properties: AppProperties

    def __init__(
            self,
            account_repository: AwardsAccountRepositoryImp = Depends(AwardsAccountRepositoryImp),
            miles_repository: AwardedMilesRepositoryImp = Depends(AwardedMilesRepositoryImp),
            client_repository: ClientRepositoryImp = Depends(ClientRepositoryImp),
            transit_repository: TransitRepositoryImp = Depends(TransitRepositoryImp),
            app_properties: AppProperties = Depends(get_app_properties)
    ):
        self.account_repository = account_repository
        self.miles_repository = miles_repository
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

        account = AwardsAccount()
        account.client = client
        account.is_active = False
        account.date = datetime.now()

        self.account_repository.save(account)

    def activate_account(self, client_id: int) -> None:
        account = self.account_repository.find_by_client(self.client_repository.get_one(client_id))

        if account is None:
            raise AttributeError("Account does not exists, client_id = " + str(client_id))

        account.is_active = True
        self.account_repository.save(account)

    def deactivate_account(self, client_id: int) -> None:
        account = self.account_repository.find_by_client(self.client_repository.get_one(client_id))

        if account is None:
            raise AttributeError("Account does not exists, client_id = " + str(client_id))

        account.is_active = False
        self.account_repository.save(account)

    def register_miles(self, client_id: int, transit_id: int) -> AwardedMiles:
        account = self.account_repository.find_by_client(self.client_repository.get_one(client_id))
        transit = self.transit_repository.get_one(transit_id)
        if transit is None:
            raise AttributeError("Transit does not exists, id = " + str(transit_id))

        now = datetime.now()
        if account == None or not account.is_active:
            return None
        else:
            miles = AwardedMiles()
            miles.transit = transit
            miles.date = datetime.now()
            miles.client = account.client
            miles.set_miles(ConstantUntil.constant_until(
                self.app_properties.default_miles_bonus,
                now + relativedelta(days=self.app_properties.miles_expiration_in_days)
            ))
            account.increase_transactions()

            self.miles_repository.save(miles)
            self.account_repository.save(account)
            return miles

    def is_sunday(self):
        return datetime.now().weekday() == 6

    def register_non_expiring_miles(self, client_id: int, miles: int) -> AwardedMiles:
        account = self.account_repository.find_by_client(self.client_repository.get_one(client_id))

        if account == None:
            raise AttributeError("Account does not exists, client_id = " + str(client_id))
        else:
            _miles = AwardedMiles()
            _miles.transit = None
            _miles.client = account.client
            _miles.set_miles(ConstantUntil.constant_until_forever(
                miles
            ))
            _miles.date = datetime.now()
            account.increase_transactions()
            self.miles_repository.save(_miles)
            self.account_repository.save(account)
            return _miles

    def remove_miles(self, client_id: int, miles: int) -> None:
        client = self.client_repository.get_one(client_id)
        account = self.account_repository.find_by_client(client)

        if account is None:
            raise AttributeError("Account does not exists, client_id = " + str(client_id))
        else:
            if self.calculate_balance(client_id) >= miles and account.is_active:
                miles_list = self.miles_repository.find_all_by_client(client)
                transits_counter = len(self.transit_repository.find_by_client(client))
                if len(client.claims) >= 3:
                    miles_list = sorted(
                        sorted(
                            miles_list,
                            key=lambda x: x.get_expiration_date() or datetime.max, reverse=True
                        ),
                        key=lambda x: x is None
                    )
                elif client.type == Client.Type.VIP:
                    miles_list = sorted(
                        miles_list,
                        key=lambda x: (x.can_expire(), x.get_expiration_date() or datetime.min)
                    )
                elif transits_counter >= 15 and self.is_sunday():
                    miles_list = sorted(
                        miles_list,
                        key=lambda x: (x.can_expire(), x.get_expiration_date() or datetime.min)
                    )
                elif transits_counter >= 15:
                    miles_list = sorted(
                        miles_list,
                        key=lambda x: (x.can_expire(), x.date)
                    )
                else:
                    miles_list = sorted(miles_list, key=lambda x: x.date)
                now: datetime = datetime.now()
                for iter in miles_list:
                    if miles <= 0:
                        break
                    if iter.can_expire() or iter.get_expiration_date() > datetime.now():
                        miles_amount: int = iter.get_miles_amount(datetime.now())
                        if miles_amount <= miles:
                            miles -= miles_amount
                            iter.remove_all(now)
                        else:
                            iter.subtract(miles, now)
                            miles = 0
                        self.miles_repository.save(iter)
            else:
                raise AttributeError("Insufficient miles, id = " + str(client_id) + ", miles requested = " + str(miles))

    def calculate_balance(self, client_id: int) -> int:
        client = self.client_repository.get_one(client_id)

        miles_list = self.miles_repository.find_all_by_client(client)
        now: datetime = datetime.now()
        sum = reduce(
            lambda a, b: a + b,
            map(
                lambda t: t.get_miles_amount(now),
                filter(
                    lambda t: t.get_expiration_date() != None and t.get_expiration_date() > datetime.now() or t.can_expire(),
                    miles_list
                )
            ),
            0
        )

        return sum

    def transfer_miles(self, from_client_id: int, to_client_id: int, miles):
        from_client = self.client_repository.get_one(from_client_id)
        account_from = self.account_repository.find_by_client(from_client)
        account_to = self.account_repository.find_by_client(self.client_repository.get_one(to_client_id))
        now: datetime = datetime.now()

        if account_from is None:
            raise AttributeError("Account does not exists, id = " + str(from_client_id))
        if account_to is None:
            raise AttributeError("Account does not exists, id = " + str(to_client_id))

        if self.calculate_balance(from_client_id) >= miles and account_from.is_active:
            miles_list = self.miles_repository.find_all_by_client(from_client)

            for iter in miles_list:
                if iter.can_expire() or iter.get_expiration_date() > datetime.now():
                    miles_amount: int = iter.get_miles_amount(now)
                    if miles_amount <= miles:
                        iter.client = account_to.client
                        miles = miles - miles_amount
                    else:
                        iter.subtract(miles, now)
                        _miles = AwardedMiles()

                        _miles.client = account_to.client
                        _miles.set_miles(iter.get_miles())

                        miles = miles - miles_amount

                        self.miles_repository.save(_miles)
                    self.miles_repository.save(iter)

            account_from.increase_transactions()
            account_to.increase_transactions()

            self.account_repository.save(account_from)
            self.account_repository.save(account_to)
