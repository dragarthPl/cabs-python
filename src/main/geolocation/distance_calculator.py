import math


class DistanceCalculator:
    def calculate_by_map(
            self, latitude_from: float, longitude_from: float, latitude_to: float, longitude_t: float) -> float:
        # ...

        return 42

    def calculate_by_geo(self, latitude_from: float, longitude_from: float, latitude_to: float, longitude_to: float):
        # https://www.geeksforgeeks.org/program-distance-two-points-earth/
        # The math module contains a function
        # named toRadians which converts from
        #  degrees to radians.
        lon1 = math.radians(longitude_from)
        lon2 = math.radians(longitude_to)
        lat1 = math.radians(latitude_from)
        lat2 = math.radians(latitude_to)

        # Haversine formula
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = math.pow(math.sin(dlat / 2), 2) + math.cos(lat1) * math.cos(lat2) * math.pow(math.sin(dlon / 2), 2)

        c = 2 * math.asin(math.sqrt(a))

        # Radius of earth in kilometers. Use 3956 for miles
        r = 6371

        # calculate the result
        distance_in_kmeters = c * r

        return distance_in_kmeters
