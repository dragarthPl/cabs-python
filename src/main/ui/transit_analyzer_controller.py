from typing import List

from dto.address_dto import AddressDTO
from dto.analyzed_addresses_dto import AnalyzedAddressesDTO
from fastapi import Depends
from fastapi_utils.cbv import cbv
from fastapi_utils.inferring_router import InferringRouter
from service.transit_analyzer import TransitAnalyzer

transit_analyzer_router = InferringRouter(tags=["TransitAnalyzerController"])

@cbv(transit_analyzer_router)
class TransitAnalyzerController:
    transit_analyzer: TransitAnalyzer = Depends(TransitAnalyzer)

    @transit_analyzer_router.get("/transit_analyze/{client_id}/{address_id}")
    def get_transit(self, client_id: int, address_id: int) -> AnalyzedAddressesDTO:
        addresses = self.transit_analyzer.analyze(client_id, address_id)
        address_dtos: List[AddressDTO] = list(map(
            lambda a: AddressDTO(**a.dict()),
            addresses
        ))
        return AnalyzedAddressesDTO(addresses=address_dtos)
