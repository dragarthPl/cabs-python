from typing import List
from uuid import UUID

from injector import inject

from geolocation.address.address import Address
from geolocation.distance import Distance
from geolocation.distance_calculator import DistanceCalculator
from geolocation.geocoding_service import GeocodingService
from ride.transit import Transit
from ride.transit_repository import TransitRepositoryImp


class ChangeDestinationService:
    transit_repository: TransitRepositoryImp
    distance_calculator: DistanceCalculator
    geocoding_service: GeocodingService

    @inject
    def __init__(
        self,
        transit_repository: TransitRepositoryImp,
        distance_calculator: DistanceCalculator,
        geocoding_service: GeocodingService,
    ):
        self.transit_repository = transit_repository
        self.distance_calculator = distance_calculator
        self.geocoding_service = geocoding_service

    def change_transit_address_to(self, request_uuid: UUID, new_address: Address, address_from: Address) -> Distance:
        # FIXME later: add some exceptions handling
        geo_from: List[float] = self.geocoding_service.geocode_address(address_from)
        geo_to: List[float] = self.geocoding_service.geocode_address(new_address)

        new_distance = Distance.of_km(float(
            self.distance_calculator.calculate_by_map(geo_from[0], geo_from[1], geo_to[0], geo_to[1])
        ))
        transit: Transit = self.transit_repository.find_by_transit_request_uuid(request_uuid)
        if transit:
            transit.change_destination(new_distance)
        return new_distance
