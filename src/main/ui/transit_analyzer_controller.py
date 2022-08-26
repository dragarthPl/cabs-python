from typing import List

from dto.address_dto import AddressDTO
from dto.analyzed_addresses_dto import AnalyzedAddressesDTO
from fastapi import Depends
from fastapi_utils.cbv import cbv
from fastapi_utils.inferring_router import InferringRouter

from repository.address_repository import AddressRepositoryImp
from transitanalyzer.graph_transit_analyzer import GraphTransitAnalyzer

transit_analyzer_router = InferringRouter(tags=["TransitAnalyzerController"])

@cbv(transit_analyzer_router)
class TransitAnalyzerController:
    graph_transit_analyzer: GraphTransitAnalyzer = Depends(GraphTransitAnalyzer)
    address_repository: AddressRepositoryImp = Depends(AddressRepositoryImp)

    @transit_analyzer_router.get("/transitAnalyze/{client_id}/{address_id}")
    def analyze(self, client_id: int, address_id: int) -> AnalyzedAddressesDTO:
        hashes: List[int] = self.graph_transit_analyzer.analyze(
            client_id,
            self.address_repository.find_hash_by_id(address_id)
        )
        address_dtos: List[AddressDTO] = list(map(
            lambda a: self.__map_to_address_dto(a),
            hashes
        ))
        return AnalyzedAddressesDTO(addresses=address_dtos)

    def __map_to_address_dto(self, hash: int) -> AddressDTO:
        return AddressDTO(self.address_repository.get_by_hash(hash.int))
