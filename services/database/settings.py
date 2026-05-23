from typing import Annotated
from pydantic import Field
from pydantic.types import SecretStr, NonNegativeInt
from pydantic_settings import SettingsConfigDict

from services.base import BaseServiceSettings


class DatabaseServiceSettings(BaseServiceSettings):
    """
    Класс настроек базы данных
    """

    model_config = SettingsConfigDict(env_prefix='database_')

    host: str = Field(default=..., frozen=True)
    port: Annotated[NonNegativeInt, Field(le=65535)] = Field(default=..., frozen=True)
    user: str = Field(default=..., frozen=True)
    password: SecretStr = Field(default=..., frozen=True)
    name: str = Field(default=..., frozen=True)
