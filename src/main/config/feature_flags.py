from pydantic import BaseSettings

from .feature import Feature


class FeatureFlagsSettings(BaseSettings):
    DRIVER_REPORT_SQL: bool = False

    class Config:
        env_file = 'feature_flags.env'
        env_file_encoding = 'utf-8'


class FeatureFlags:
    feature_flags_settings: FeatureFlagsSettings = FeatureFlagsSettings()

    @property
    def DRIVER_REPORT_SQL(self):
        return Feature(
            self.feature_flags_settings.DRIVER_REPORT_SQL,
            "Driver report created using sql query"
        )

def get_feature_flags():
    return FeatureFlags()
