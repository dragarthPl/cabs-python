from datetime import datetime

from sqlmodel import Field
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

    #@ManyToOne
    client: Client = Field(default=None, foreign_key="client.id")
    miles: int = Field(sa_column=Column(Integer, nullable=False))
    date: datetime = Field(default=datetime.now(), sa_column=Column(DateTime, nullable=False))
    expiration_date: datetime
    is_special: bool
    transit: Transit = Field(default=None, foreign_key="transit.id")
