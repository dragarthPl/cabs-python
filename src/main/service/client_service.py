from dto.client_dto import ClientDTO
from entity import Client
from fastapi import Depends
from repository.client_repository import ClientRepositoryImp


class ClientService:
    client_repository: ClientRepositoryImp

    def __init__(
            self,
            client_repository: ClientRepositoryImp = Depends(ClientRepositoryImp),
    ):
        self.client_repository = client_repository

    # @Transactional
    def register_client(self, name, last_name, a_type, default_payment_type):
        client: Client = Client()
        client.name = name
        client.last_name = last_name
        client.type = a_type
        client.default_payment_type = default_payment_type
        return self.client_repository.save(client)

    # @Transactional
    def change_default_payment_type(self, client_id: int, payment_type: Client.PaymentType):
        client = self.client_repository.get_one(client_id)
        if client is None:
            raise AttributeError("Client does not exists, id = " + str(client_id))
        client.default_payment_type = payment_type
        self.client_repository.save(client)

    # @Transactional
    def upgrade_to_vip(self, client_id: int):
        client = self.client_repository.get_one(client_id)
        if client is None:
            raise AttributeError("Client does not exists, id = " + str(client_id))
        client.type = Client.Type.VIP
        self.client_repository.save(client)

    # @Transactional
    def downgrade_to_regular(self, client_id):
        client = self.client_repository.get_one(client_id)
        if client is None:
            raise AttributeError("Client does not exists, id = " + str(client_id))
        client.type = Client.Type.NORMAL
        self.client_repository.save(client)

    # @Transactional
    def load(self, client_id: int) -> ClientDTO:
        return ClientDTO(**self.client_repository.get_one(client_id).dict())
