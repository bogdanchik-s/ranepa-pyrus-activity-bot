from pydantic import SecretStr, Field
from pydantic_settings import SettingsConfigDict
from services.base import BaseServiceSettings


class SQSServiceSettings(BaseServiceSettings):
    """
    Класс настроек `SQSService`
    """

    model_config = SettingsConfigDict(env_prefix='sqs_')

    host: str = Field(default=..., frozen=True)
    region: str = Field(default=..., frozen=True)
    queue_name: str = Field(default=..., frozen=True)
    queue_url: str = Field(default=..., frozen=True)
    access_key_id: SecretStr = Field(default=..., frozen=True)
    secret_access_key: SecretStr = Field(default=..., frozen=True)
