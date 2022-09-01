from datetime import datetime

import pytz
from fastapi import Depends

from distance.distance import Distance
from dto.address_dto import AddressDTO
from dto.client_dto import ClientDTO
from dto.transit_dto import TransitDTO
from entity import Driver, Client, Transit
from money import Money
from repository.transit_repository import TransitRepositoryImp
from service.transit_service import TransitService
from transitdetails.transit_details_facade import TransitDetailsFacade


class TransitFixture:
    transit_service: TransitService
    transit_repository: TransitRepositoryImp
    transit_details_facade: TransitDetailsFacade

    def __init__(
        self,
        transit_service: TransitService = Depends(TransitService),
        transit_repository: TransitRepositoryImp = Depends(TransitRepositoryImp),
        transit_details_facade: TransitDetailsFacade = Depends(TransitDetailsFacade),
    ):
        self.transit_service = transit_service
        self.transit_repository = transit_repository
        self.transit_details_facade = transit_details_facade

    def a_transit(self, driver: Driver, price: int, when: datetime, client: Client) -> Transit:
        date_time = when.astimezone(pytz.UTC)
        transit: Transit = Transit(
            when=date_time,
            distance=Distance.ZERO,
        )
        transit.set_price(Money(price))
        transit.propose_to(driver)
        transit.accept_by(driver, datetime.now())
        transit = self.transit_repository.save(transit)
        self.transit_details_facade.transit_requested(
            when=date_time,
            transit_id=transit.id,
            address_from=None,
            address_to=None,
            distance=Distance.ZERO,
            client=client,
            car_class=None,
            estimated_price=Money(price),
            tariff=transit.get_tariff(),
        )
        return transit

    def a_transit_when(self, driver: Driver, price: int) -> Transit:
        return self.a_transit(driver, price, datetime.now(), None)

    def a_transit_dto_for_client(self, client: Client, address_from: AddressDTO, address_to: AddressDTO):
        transit_dto = TransitDTO()
        transit_dto.client_dto = ClientDTO(**client.dict())
        transit_dto.address_from = address_from
        transit_dto.address_to = address_to
        return transit_dto
