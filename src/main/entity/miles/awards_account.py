from __future__ import annotations

from datetime import datetime
from functools import reduce
from typing import Optional, Set, Any, List, Callable

from entity import Client, ConstantUntil, AwardedMiles
from sqlalchemy import Boolean, Column, DateTime, Integer
from sqlalchemy.orm import relationship, backref
from sqlmodel import Field, Relationship

from common.base_entity import BaseEntity


class AwardsAccount(BaseEntity, table=True):
    __table_args__ = {'extend_existing': True}

    # @OneToOne
    client_id: Optional[int] = Field(default=None, foreign_key="client.id")
    client: Optional[Client] = Relationship(sa_relationship=relationship("Client", backref=backref("awards_account", uselist=False)))
    #@Column(nullable = false)
    date: datetime = Field(default=datetime.now(), sa_column=Column(DateTime, nullable=False))
    # @Column(nullable = false)
    is_active: bool = Field(default=False, sa_column=Column(Boolean, nullable=False))
    #@Column(nullable = false)
    transactions: int = Field(default=0, sa_column=Column(Integer, nullable=False))

    # @OneToMany(mappedBy = "account")
    #@Fetch(value=FetchMode.JOIN)
    miles: Set[AwardedMiles] = Relationship(
        sa_relationship=relationship(
            "entity.miles.awarded_miles.AwardedMiles", back_populates="account")
    )

    def __init__(self, client: Client, is_active: bool, when: datetime, **data: Any):
        super().__init__(**data)
        self.client = client
        self.is_active = is_active
        self.date = when

    @staticmethod
    def not_active_account(client: Client, when: datetime):
        return AwardsAccount(client, False, when)

    def add_expiring_miles(self, amount: int, expire_at: datetime, transit: Transit, when: datetime) -> AwardedMiles:
        expiring_miles = AwardedMiles(
            awards_account=self,
            transit=transit,
            client=self.client,
            when=when,
            constant_until=ConstantUntil.constant_until(amount, expire_at)
        )
        self.miles.append(expiring_miles)
        self.transactions += 1
        return expiring_miles

    def add_non_expiring_miles(self, amount: int, when: datetime) -> AwardedMiles:
        non_expiring_miles = AwardedMiles(
            awards_account=self,
            transit=None,
            client=self.client,
            when=when,
            constant_until=ConstantUntil.constant_until_forever(amount)
        )
        self.miles.append(non_expiring_miles)
        self.transactions += 1
        return non_expiring_miles

    def calculate_balance(self, at: datetime) -> int:
        return reduce(
            lambda a, b: a + b,
            map(
                lambda t: t.get_miles_amount(at),
                filter(
                    lambda
                        t: t.get_expiration_date() != None
                           and t.get_expiration_date().utctimetuple() > at.utctimetuple() or t.can_expire(),
                    self.miles
                )
            ),
            0
        )

    def remove(
        self,
        miles: int,
        when: datetime,
        strategy: Callable
    ) -> None:
        if self.calculate_balance(when) >= miles and self.is_active:
            miles_list = list(self.miles)
            # if claims_counter >= 3:
            #     miles_list = sorted(
            #         sorted(
            #             miles_list,
            #             key=lambda x: x.get_expiration_date() or datetime.max, reverse=True
            #         ),
            #         key=lambda x: x is None
            #     )
            # elif client_type == Client.Type.VIP:
            #     miles_list = sorted(
            #         miles_list,
            #         key=lambda x: (x.can_expire(), x.get_expiration_date() or datetime.min)
            #     )
            # elif transits_counter >= 15 and is_sunday:
            #     miles_list = sorted(
            #         miles_list,
            #         key=lambda x: (x.can_expire(), x.get_expiration_date() or datetime.min)
            #     )
            # elif transits_counter >= 15:
            #     miles_list = sorted(
            #         miles_list,
            #         key=lambda x: (x.can_expire(), x.date)
            #     )
            # else:
            #     miles_list = sorted(miles_list, key=lambda x: x.date)
            miles_list.sort(key=strategy)
            for iter in miles_list:
                if miles <= 0:
                    break
                if iter.can_expire() or iter.get_expiration_date() > datetime.now():
                    miles_amount: int = iter.get_miles_amount(datetime.now())
                    if miles_amount <= miles:
                        miles -= miles_amount
                        iter.remove_all(when)
                    else:
                        iter.subtract(miles, when)
                        miles = 0
        else:
            raise AttributeError(f"Insufficient miles, id = {self.client_id}, miles requested = {miles}")

    def move_miles_to(self, account_to: 'AwardsAccount', amount: int, when: datetime) -> None:
        if self.calculate_balance(when) >= amount and self.is_active:
            for iter in self.miles:
                miles_amount: int = iter.get_miles_amount(when)
                if miles_amount <= amount:
                    iter.transfer_to(account_to)
                    amount = amount - miles_amount
                else:
                    iter.subtract(amount, when)
                    iter.transfer_to(account_to)
                    amount = amount - iter.get_miles_amount(when)
            self.transactions += 1
            account_to.transactions += 1

    def activate(self) -> None:
        self.is_active = True

    def deactivate(self) -> None:
        self.is_active = False

    def __eq__(self, o):
        if not isinstance(o, AwardsAccount):
            return False
        return self.id is not None and self.id == o.id

    def get_miles(self) -> List[AwardedMiles]:
        return list(self.miles)
