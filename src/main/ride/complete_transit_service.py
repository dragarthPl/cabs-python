from typing import List
from uuid import UUID

from injector import inject

from geolocation.address.address import Address
from geolocation.distance import Distance
from geolocation.distance_calculator import DistanceCalculator
from geolocation.geocoding_service import GeocodingService
from money import Money
from ride.transit import Transit
from ride.transit_repository import TransitRepositoryImp


class CompleteTransitService:
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

    def complete_transit(
            self,
            driver_id: int,
            request_uuid: UUID,
            address_from: Address,
            destination_address: Address
    ) -> Money:
        transit: Transit = self.transit_repository.find_by_transit_request_uuid(request_uuid)

        if transit is None:
            raise AttributeError(f"Transit does not exist, id = {request_uuid}")

        # FIXME later: add some exceptions handling
        geo_from: List[float] = self.geocoding_service.geocode_address(address_from)
        geo_to: List[float] = self.geocoding_service.geocode_address(destination_address)
        distance: Distance = Distance.of_km(self.distance_calculator.calculate_by_map(
            geo_from[0],
            geo_from[1],
            geo_to[0],
            geo_to[1]
        ))
        final_price: Money = transit.complete_ride_at(distance)
        self.transit_repository.save(transit)
        return final_price
