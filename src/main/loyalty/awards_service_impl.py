import sys
from datetime import datetime
from typing import Callable, Optional

from injector import inject

from config.app_properties import AppProperties
from dateutil.relativedelta import relativedelta

from crm.claims.claim_service import ClaimService
from loyalty.awards_account_dto import AwardsAccountDTO
from dto.client_dto import ClientDTO
from entity import Client
from loyalty.awarded_miles import AwardedMiles
from loyalty.awards_account import AwardsAccount
from loyalty.awards_account_repository import AwardsAccountRepositoryImp
from repository.client_repository import ClientRepositoryImp
from repository.transit_repository import TransitRepositoryImp
from loyalty.awards_service import AwardsService
from service.client_service import ClientService


class AwardsServiceImpl(AwardsService):
    account_repository: AwardsAccountRepositoryImp
    transit_repository: TransitRepositoryImp
    app_properties: AppProperties

    client_service: ClientService
    __claim_service: Optional[ClaimService] = None

    @inject
    def __init__(
            self,
            account_repository: AwardsAccountRepositoryImp,
            client_repository: ClientRepositoryImp,
            transit_repository: TransitRepositoryImp,
            app_properties: AppProperties,
            client_service: ClientService,
    ):
        self.account_repository = account_repository
        self.client_repository = client_repository
        self.transit_repository = transit_repository
        self.app_properties = app_properties
        self.client_service = client_service

    @property
    def claim_service(self):
        if not self.__claim_service:
            self.set_clim_service()
        return self.__claim_service

    def set_clim_service(self):
        from cabs_application import app
        self.__claim_service = app.state.injector.get(ClaimService)

    def find_by(self, client_id: int) -> AwardsAccountDTO:
        return AwardsAccountDTO(
            awards_account=self.account_repository.find_by_client_id(client_id),
            client_dto=self.client_service.load(client_id),
        )

    def register_to_program(self, client_id: int) -> None:
        client = self.client_service.load(client_id)

        if client is None:
            raise AttributeError("Client does not exists, id = " + str(client_id))

        account = AwardsAccount.not_active_account(client_id, datetime.now())
        self.account_repository.save(account)

    def activate_account(self, client_id: int) -> None:
        account = self.account_repository.find_by_client_id(client_id)

        if account is None:
            raise AttributeError("Account does not exists, client_id = " + str(client_id))

        account.activate()
        self.account_repository.save(account)

    def deactivate_account(self, client_id: int) -> None:
        account = self.account_repository.find_by_client_id(client_id)

        if account is None:
            raise AttributeError("Account does not exists, client_id = " + str(client_id))

        account.deactivate()
        self.account_repository.save(account)

    def register_miles(self, client_id: int, transit_id: int) -> AwardedMiles:
        account = self.account_repository.find_by_client_id(client_id)
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
                transit_id,
                datetime.now()
            )
            self.account_repository.save(account)
            return miles

    def is_sunday(self):
        return datetime.now().weekday() == 6

    def register_non_expiring_miles(self, client_id: int, miles: int) -> AwardedMiles:
        account = self.account_repository.find_by_client_id(client_id)

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
        account: AwardsAccount = self.account_repository.find_by_client_id(client_id)
        client: ClientDTO = self.client_service.load(client_id)

        if account is None:
            raise AttributeError("Account does not exists, client_id = " + str(client_id))
        else:
            number_of_claims: int = self.claim_service.get_number_of_claims(client_id)
            account.remove(
                miles,
                datetime.now(),
                self.choose_strategy(
                    len(self.transit_repository.find_by_client_id(client_id)),
                    number_of_claims,
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
        account = self.account_repository.find_by_client_id(client_id)
        return account.calculate_balance(datetime.now())

    def transfer_miles(self, from_client_id: int, to_client_id: int, miles):
        account_from = self.account_repository.find_by_client_id(from_client_id)
        account_to = self.account_repository.find_by_client_id(to_client_id)
        now: datetime = datetime.now()

        if account_from is None:
            raise AttributeError("Account does not exists, id = " + str(from_client_id))
        if account_to is None:
            raise AttributeError("Account does not exists, id = " + str(to_client_id))

        account_from.move_miles_to(account_to, miles, now)
        self.account_repository.save(account_from)
        self.account_repository.save(account_to)
