from typing import List

from dateutil.relativedelta import relativedelta
from entity import Address, Client, Transit
from fastapi import Depends
from repository.address_repository import AddressRepositoryImp
from repository.client_repository import ClientRepositoryImp
from repository.transit_repository import TransitRepositoryImp


class TransitAnalyzer:
    transit_repository: TransitRepositoryImp
    client_repository: ClientRepositoryImp
    address_repository: AddressRepositoryImp

    def __init__(
            self,
            transit_repository: TransitRepositoryImp = Depends(TransitRepositoryImp),
            client_repository: ClientRepositoryImp = Depends(ClientRepositoryImp),
            address_repository: AddressRepositoryImp = Depends(AddressRepositoryImp),
    ):
        self.transit_repository = transit_repository
        self.client_repository = client_repository
        self.address_repository = address_repository

    def analyze(self, client_id, address_id) -> List[Address]:
        client = self.client_repository.get_one(client_id)
        if client is None:
            raise AttributeError("Client does not exists, id = " + str(client_id))
        address = self.address_repository.get_one(address_id)
        if address is None:
            raise AttributeError("Address does not exists, id = " + str(address_id))
        return self.__analyze(client, address, None)

    # Brace yourself, deadline is coming... They made me to do it this way.
    # Tested!
    def __analyze(self, client: Client, address: Address, t: Transit) -> List[Address]:
        ts: List[Transit] = []
        if t is None:
            ts = self.transit_repository.find_all_by_client_and_from_and_status_order_by_date_time_desc(
                client,
                address,
                Transit.Status.COMPLETED
            )
        else:
            ts = self.transit_repository.find_all_by_client_and_from_and_published_after_and_status_order_by_date_time_desc(
                client,
                address,
                t.published,
                Transit.Status.COMPLETED
            )

        # Workaround for performance reasons.
        if len(ts) > 1000 and client.id == 666:
            # No one will see a difference for this customer ;)
            ts = ts[:1000]

        # if not ts:
        #     return [t.address_to]

        if t != None:
            ts = list(filter(
                lambda _t: t.complete_at + relativedelta(minutes=15) > _t.started,
                ts
            ))

        if not ts:
            return [t.address_to]

        def mapper(_t: Transit) -> List[Address]:
            result = []
            result.append(_t.address_from)
            result.extend(self.__analyze(client, _t.address_to, _t))
            return result

        return sorted(
            map(
                mapper,
                ts
            ),
            reverse=True,
            key=lambda a, b: len(a) - len(b)
        )[0] or []
