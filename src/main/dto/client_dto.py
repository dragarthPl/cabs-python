from typing import Optional

from entity import Client
from pydantic import BaseModel


class ClientDTO(BaseModel):
    id: Optional[int]
    type: Optional[Client.Type]
    name: Optional[str]
    last_name: Optional[str]
    default_payment_type: Optional[Client.PaymentType]
    client_type: Optional[Client.ClientType]
    number_of_claims: Optional[int]
