import math
from typing import List
from uuid import UUID

from injector import inject

from geolocation.address.address import Address
from geolocation.address.address_repository import AddressRepositoryImp
from geolocation.distance import Distance
from geolocation.distance_calculator import DistanceCalculator
from geolocation.geocoding_service import GeocodingService
from ride.transit_demand import TransitDemand
from ride.transit_demand_repository import TransitDemandRepository


class ChangePickupService:
    distance_calculator: DistanceCalculator
    geocoding_service: GeocodingService
    address_repository: AddressRepositoryImp
    transit_demand_repository: TransitDemandRepository

    @inject
    def __init__(
        self,
        distance_calculator: DistanceCalculator,
        geocoding_service: GeocodingService,
        address_repository: AddressRepositoryImp,
        transit_demand_repository: TransitDemandRepository,
    ):
        self.distance_calculator = distance_calculator
        self.geocoding_service = geocoding_service
        self.address_repository = address_repository
        self.transit_demand_repository = transit_demand_repository


    def change_transit_address_from(self, request_uuid: UUID, new_address: Address, old_address: Address) -> Distance:
        new_address = self.address_repository.save(new_address)
        transit_demand: TransitDemand = self.transit_demand_repository.find_by_transit_request_uuid(request_uuid)
        if transit_demand is None:
            raise AttributeError("Transit does not exist, id = " + str(request_uuid))

        # FIXME later: add some exceptions handling
        geo_from_new: List[float] = self.geocoding_service.geocode_address(new_address)
        geo_from_old: List[float] = self.geocoding_service.geocode_address(old_address)

        # https://www.geeksforgeeks.org/program-distance-two-points-earth/
        # The math module contains a function
        # named toRadians which converts from
        # degrees to radians.
        lon1: float = math.radians(geo_from_new[1])
        lon2: float = math.radians(geo_from_old[1])
        lat1: float = math.radians(geo_from_new[0])
        lat2: float = math.radians(geo_from_old[0])

        # Haversine formula
        dlon: float = lon2 - lon1
        dlat: float = lat2 - lat1
        a: float = math.pow(math.sin(dlat / 2), 2) + math.cos(lat1) * math.cos(lat2) * math.pow(math.sin(dlon / 2), 2)

        c = 2 * math.asin(math.sqrt(a))

        # Radius of earth in kilometers. Use 3956 for miles
        r = 6371

        # calculate the result
        distance_in_kmeters = c * r

        new_distance = Distance.of_km(float(
            self.distance_calculator.calculate_by_map(
                geo_from_new[0],
                geo_from_new[1],
                geo_from_old[0],
                geo_from_old[1]
            )
        ))
        transit_demand.change_pickup(distance_in_kmeters)
        return new_distance
