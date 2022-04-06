from functools import lru_cache

from pydantic import BaseSettings


class AppProperties(BaseSettings):
    no_of_transits_for_claim_automatic_refund: int
    automatic_refund_for_vip_threshold: int
    min_no_of_cars_for_eco_class: int
    miles_expiration_in_days: int = 365
    default_miles_bonus: int = 10
    sqlite_url: str

    class Config:
        env_file = 'dev.env'
        env_file_encoding = 'utf-8'


@lru_cache()
def get_app_properties():
    return AppProperties()
