from typing import Optional
from pydantic import Field
from pydantic.types import SecretStr, NonNegativeInt
from pydantic_settings import SettingsConfigDict

from services.base import BaseServiceSettings


class PyrusServiceSettings(BaseServiceSettings):
    """
    Класс настроек системы Pyrus
    """

    model_config = SettingsConfigDict(env_prefix='pyrus_')

    bot_id: NonNegativeInt = Field(default=..., frozen=True)
    bot_login: str = Field(default=..., frozen=True)
    bot_secret_key: SecretStr = Field(default=..., frozen=True)
    access_token: Optional[SecretStr] = Field(default=None, frozen=False)
