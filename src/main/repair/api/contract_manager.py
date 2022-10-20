from injector import inject

from party.api.party_id import PartyId
from party.infra.party_relationship_repository_impl import PartyRelationshipRepositoryImpl
from party.infra.party_repository_impl import PartyRepositoryImpl
from party.model.party.party import Party
from party.model.party.party_relationship_repository import PartyRelationshipRepository
from party.model.party.party_repository import PartyRepository
from repair.model.dict.party_relationships_dictionary import PartyRelationshipsDictionary
from repair.model.dict.party_roles_dictionary import PartyRolesDictionary


class ContractManager:
    party_repository: PartyRepository
    party_relationship_repository: PartyRelationshipRepository

    @inject
    def __init__(
        self,
        party_repository: PartyRepository,
        party_relationship_repository: PartyRelationshipRepository,
    ):
        self.party_repository = party_repository
        self.party_relationship_repository = party_relationship_repository

    def extended_warranty_contract_signed(self, insurer_id: PartyId, vehicle_id: PartyId):
        insurer: Party = self.party_repository.put(insurer_id.to_uuid())
        vehicle: Party = self.party_repository.put(vehicle_id.to_uuid())

        self.party_relationship_repository.put(
            PartyRelationshipsDictionary.REPAIR.name,
            PartyRolesDictionary.INSURER.get_role_name(), insurer,
            PartyRolesDictionary.INSURED.get_role_name(), vehicle
        )

    def manufacturer_warranty_registered(self, distributor_id: PartyId, vehicle_id: PartyId):
        distributor: Party = self.party_repository.put(distributor_id.to_uuid())
        vehicle: Party = self.party_repository.put(vehicle_id.to_uuid())

        self.party_relationship_repository.put(
            PartyRelationshipsDictionary.REPAIR.name,
            PartyRolesDictionary.GUARANTOR.get_role_name(), distributor,
            PartyRolesDictionary.CUSTOMER.get_role_name(), vehicle
        )
