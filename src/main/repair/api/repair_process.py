from typing import Optional

from fastapi import Depends

from party.api.party_mapper import PartyMapper
from party.api.role_object_factory import RoleObjectFactory
from party.model.party.party_relationship import PartyRelationship
from repair.api.repair_request import RepairRequest
from repair.api.resolve_result import ResolveResult
from repair.model.dict.party_relationships_dictionary import PartyRelationshipsDictionary
from repair.model.roles.repair.repairing_result import RepairingResult
from repair.model.roles.repair.role_for_repairer import RoleForRepairer


class RepairProcess:
    party_mapper: PartyMapper

    def __init__(self, party_mapper: PartyMapper = Depends(PartyMapper)):
        self.party_mapper = party_mapper

    def resolve(self, repair_request: RepairRequest) -> ResolveResult:
        return list(map(
            lambda repairing_result: ResolveResult(
                ResolveResult.Status.SUCCESS,
                repairing_result.handling_party,
                repairing_result.total_cost,
                repairing_result.handled_parts
            ) if repairing_result else None,
            map(
                lambda role: role.handle(repair_request) if role else None,
                map(
                    lambda rof: rof.get_role(RoleForRepairer),
                    map(
                        lambda relation: RoleObjectFactory.from_relationship(relation),
                        self.party_mapper.map_relation(
                            repair_request.vehicle,
                            PartyRelationshipsDictionary.REPAIR.name
                        )
                    )
                )
            )
        ))[0] or ResolveResult(ResolveResult.Status.ERROR)

    def resolve_oldschool_version(self, repair_request: RepairRequest) -> ResolveResult:
        # who is responsible for repairing the vehicle
        relationship: Optional[PartyRelationship] = self.party_mapper.map_relation(
            repair_request.vehicle,
            PartyRelationshipsDictionary.REPAIR.name
        )
        if relationship:
            role_object_factory: RoleObjectFactory = RoleObjectFactory.from_relationship(relationship)
            # dynamically assigned rules
            role: Optional[RoleForRepairer] = role_object_factory.get_role(RoleForRepairer)
            if role:
                # actual repair request handling
                repairing_result: RepairingResult = role.handle(repair_request);
                return ResolveResult(
                    ResolveResult.Status.SUCCESS,
                    repairing_result.handling_party,
                    repairing_result.total_cost,
                    repairing_result.handled_parts,
                )
        return ResolveResult(ResolveResult.Status.ERROR)
