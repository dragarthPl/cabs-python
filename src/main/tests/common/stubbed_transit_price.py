from fastapi import Depends

from entity import Transit
from money import Money
from repository.transit_repository import TransitRepositoryImp


class StubbedTransitPrice:
    transit_repository: TransitRepositoryImp

    def __init__(self, transit_repository: TransitRepositoryImp = Depends(TransitRepositoryImp)):
        self.transit_repository = transit_repository

    def stub(self, transit_id: int, faked: Money) -> Transit:
        transit: Transit = self.transit_repository.get_one(transit_id)
        transit.price = faked
        return transit
