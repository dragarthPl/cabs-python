from datetime import datetime
from typing import List

from injector import inject

from geolocation.address.address import Address
from geolocation.distance import Distance
from geolocation.distance_calculator import DistanceCalculator
from geolocation.geocoding_service import GeocodingService
from pricing.tariff import Tariff
from pricing.tariffs import Tariffs
from ride.request_for_transit import RequestForTransit
from ride.request_for_transit_repository import RequestForTransitRepository


class RequestTransitService:
    distance_calculator: DistanceCalculator
    geocoding_service: GeocodingService
    request_for_transit_repository: RequestForTransitRepository
    tariffs: Tariffs

    @inject
    def __init__(
        self,
        distance_calculator: DistanceCalculator,
        geocoding_service: GeocodingService,
        request_for_transit_repository: RequestForTransitRepository,
        tariffs: Tariffs,
    ):
        self.distance_calculator = distance_calculator
        self.geocoding_service = geocoding_service
        self.request_for_transit_repository = request_for_transit_repository
        self.tariffs = tariffs

    def create_request_for_transit(self, address_from: Address, address_to: Address):
        # FIXME later: add some exceptions handling
        geo_from: List[float] = self.geocoding_service.geocode_address(address_from)
        geo_to: List[float] = self.geocoding_service.geocode_address(address_to)
        distance: Distance = Distance.of_km((self.distance_calculator.calculate_by_map(
            geo_from[0],
            geo_from[1],
            geo_to[0],
            geo_to[1]
        )))
        now: datetime = datetime.now()
        tariff: Tariff = self.choose_tariff(now)
        return self.request_for_transit_repository.save(RequestForTransit(tariff=tariff, distance=distance))

    def choose_tariff(self, when: datetime) -> Tariff:
        return self.tariffs.choose(when)
