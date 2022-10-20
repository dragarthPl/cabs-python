from injector import inject

from entity import Transit
from money import Money
from repository.transit_repository import TransitRepositoryImp


class StubbedTransitPrice:
    transit_repository: TransitRepositoryImp

    @inject
    def __init__(self, transit_repository: TransitRepositoryImp):
        self.transit_repository = transit_repository

    def stub(self, transit_id: int, faked: Money) -> Transit:
        transit: Transit = self.transit_repository.get_one(transit_id)
        transit.set_price(faked)
        return transit
