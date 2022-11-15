from typing import Optional

from pydantic import BaseModel

from crm.client import Client


class ClientDTO(BaseModel):
    id: Optional[int]
    type: Optional[Client.Type]
    name: Optional[str]
    last_name: Optional[str]
    default_payment_type: Optional[Client.PaymentType]
    client_type: Optional[Client.ClientType]
    number_of_claims: Optional[int]
    is_occupied: Optional[bool]
