from datetime import datetime
from typing import Optional

from sqlalchemy.orm import relationship
from sqlmodel import Field, Relationship
from sqlalchemy import Column, Integer, DateTime

from common.base_entity import BaseEntity
from entity import Client
from entity import Transit


class AwardedMiles(BaseEntity, table=True):
    __table_args__ = {'extend_existing': True}
    # Aggregate
    # 1. mile celowo są osobno, aby się mogło rozjechać na ich wydawaniu -> docelowo: kolekcja VOs w agregacie

    # VO
    # 1. miles + expirationDate -> VO przykrywające logikę walidacji, czy nie przekroczono daty ważności punktów
    # 2. wydzielenie interfejsu Miles -> różne VO z różną logiką, np. ExpirableMiles, NonExpirableMiles, LinearExpirableMiles

    # @ManyToOne
    client_id: Optional[int] = Field(default=None, foreign_key="client.id")
    client: Optional[Client] = Relationship(
        sa_relationship=relationship(
            "entity.client.Client")
    )

    # @Column(nullable = false)
    miles: int = Field(sa_column=Column(Integer, nullable=False))
    # @Column(nullable = false)
    date: datetime = Field(default=datetime.now(), sa_column=Column(DateTime, nullable=False))
    expiration_date: Optional[datetime]
    is_special: Optional[bool]
    # @ManyToOne
    transit_id: Optional[int] = Field(default=None, foreign_key="transit.id")
    transit: Optional[Transit] = Relationship(
        sa_relationship_kwargs=dict(foreign_keys="[AwardedMiles.transit_id]")
    )

    def __eq__(self, o):
        if not isinstance(o, AwardedMiles):
            return False
        return self.id is not None and self.id == o.id
