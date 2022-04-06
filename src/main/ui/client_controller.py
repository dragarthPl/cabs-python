from dto.client_dto import ClientDTO
from entity.client import Client
from fastapi import Depends, Body
from fastapi_utils.cbv import cbv
from fastapi_utils.inferring_router import InferringRouter
from service.client_service import ClientService

client_router = InferringRouter(tags=["ClientController"])

@cbv(client_router)
class ClientController:

    client_service: ClientService = Depends(ClientService)

    @client_router.post("/clients")
    def register(self, dto: ClientDTO) -> ClientDTO:
        c: Client = self.client_service.register_client(
            dto.name, dto.last_name, dto.type, dto.default_payment_type)
        return self.client_service.load(c.id)

    @client_router.get("/clients/{client_id}")
    def find(self, client_id: int) -> ClientDTO:
        return self.client_service.load(client_id)

    @client_router.post("/clients/{client_id}/upgrade")
    def upgrade_to_vip(self, client_id: int) -> ClientDTO:
        self.client_service.upgrade_to_vip(client_id)
        return self.client_service.load(client_id)

    @client_router.post("/clients/{client_id}/downgrade")
    def downgrade(self, client_id: int) -> ClientDTO:
        self.client_service.downgrade_to_regular(client_id)
        return self.client_service.load(client_id)

    @client_router.post("/clients/{client_id}/changeDefaultPaymentType")
    def change_default_payment_type(self, client_id: int, dto: ClientDTO) -> ClientDTO:
        self.client_service.change_default_payment_type(client_id, dto.default_payment_type)
        return self.client_service.load(client_id)
