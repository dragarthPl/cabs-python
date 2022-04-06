from entity import Client


class ClientDTO:
    _id: int
    type: Client.Type
    name: str
    last_name: str
    default_payment_type: Client.PaymentType
    client_type: Client.ClientType

    def __init__(self, client: Client):
        self._id = client.get_id()
        self.type = client.a_type
        self.name = client.name
        self.last_name = client.last_name
        self.default_payment_type = client.default_payment_type
        self.client_type = client.client_type
