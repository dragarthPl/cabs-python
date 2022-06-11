from typing import Set
from unittest import TestCase

from fastapi.params import Depends

from core.database import create_db_and_tables, drop_db_and_tables
from party.api.party_id import PartyId
from repair.api.contract_manager import ContractManager
from repair.api.repair_process import RepairProcess
from repair.api.repair_request import RepairRequest
from repair.api.resolve_result import ResolveResult
from repair.legacy.parts.parts import Parts
from tests.repair.api.vehicle_repair_assert import VehicleRepairAssert
from tests.common.fixtures import DependencyResolver

dependency_resolver = DependencyResolver()


class TestRepairProcess(TestCase):
    vehicle_repair_process: RepairProcess = dependency_resolver.resolve_dependency(
        Depends(RepairProcess)
    )
    contract_manager: ContractManager = dependency_resolver.resolve_dependency(
        Depends(ContractManager)
    )

    vehicle: PartyId = PartyId()
    handling_party: PartyId = PartyId()

    def setUp(self):
        create_db_and_tables()

    def test_warranty_by_insurance_covers_all_but_paint(self):
        # given
        self.contract_manager.extended_warranty_contract_signed(self.handling_party, self.vehicle)

        parts: Set[Parts] = {Parts.ENGINE, Parts.GEARBOX, Parts.PAINT, Parts.SUSPENSION}
        repair_request: RepairRequest = RepairRequest(self.vehicle, parts)
        # when
        result: ResolveResult = self.vehicle_repair_process.resolve(repair_request)
        # then
        VehicleRepairAssert(result).by(self.handling_party).free().all_parts_but(parts, (Parts.PAINT,))

    def test_manufacturer_warranty_covers_all(self):
        # given
        self.contract_manager.manufacturer_warranty_registered(self.handling_party, self.vehicle)

        parts: Set[Parts] = {Parts.ENGINE, Parts.GEARBOX, Parts.PAINT, Parts.SUSPENSION}
        repair_request: RepairRequest = RepairRequest(self.vehicle, parts)
        # when
        result: ResolveResult = self.vehicle_repair_process.resolve(repair_request)
        # then
        VehicleRepairAssert(result).by(self.handling_party).free().all_parts(parts)

    def tearDown(self) -> None:
        drop_db_and_tables()
