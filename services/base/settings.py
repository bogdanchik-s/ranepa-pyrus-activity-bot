from typing import Any
from collections.abc import Callable
from pydantic import field_serializer
from pydantic.types import SecretStr
from pydantic_settings import BaseSettings as PydanticBaseSettings, SettingsConfigDict


class BaseServiceSettings(PydanticBaseSettings):
    """
    Базовый класс настроек приложения
    """

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore'
    )

    @field_serializer('*', mode='wrap', when_used='json')
    def secret_str_serializer(self, value: Any, handler: Callable[..., Any]) -> Any | str:
        if isinstance(value, SecretStr):
            return value.get_secret_value()
        else:
            return handler(value)
    
    def update(self, data, /) -> None:
        if not isinstance(data, dict):
            raise ValueError(f'[{self.__class__.__name__}] The data to update must be a `dict` instance.')
    
        for field_name, field_value in data.items():
            field = self.__class__.model_fields.get(field_name)
            
            if field is not None and not field.frozen:
                setattr(self, field_name, field_value)
