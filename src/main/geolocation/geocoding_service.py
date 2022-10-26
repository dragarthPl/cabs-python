from typing import List, Optional


class GeocodingService:
    def geocode_address(self, address_from) -> List[Optional[float]]:
        # TODO...call do zewnętrznego serwisu

        geocoded: List[Optional[float]] = [None, None]

        geocoded[0] = 1.0  # latitude
        geocoded[1] = 1.0  # longitude

        return geocoded
