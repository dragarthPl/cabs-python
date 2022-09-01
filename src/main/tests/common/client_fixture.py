from fastapi import Depends

from entity import Client
from repository.client_repository import ClientRepositoryImp


class ClientFixture:
    client_repository: ClientRepositoryImp

    def __init__(
        self,
        client_repository: ClientRepositoryImp = Depends(ClientRepositoryImp),
    ):
        self.client_repository = client_repository

    def a_client_default(self) -> Client:
        return self.client_repository.save(Client())

    def a_client(self, client_type: Client.Type) -> Client:
        client: Client = Client()
        client.type = client_type
        return self.client_repository.save(client)