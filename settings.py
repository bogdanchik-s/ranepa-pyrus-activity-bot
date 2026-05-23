import os

from io import TextIOWrapper
from typing import Any
from pydantic import Field
from pydantic_settings import BaseSettings as PydanticBaseSettings, SettingsConfigDict

from common.types import Seconds
from services.database import DatabaseServiceSettings
from services.sqs import SQSServiceSettings


ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
TEMP_DIR = os.path.join(ROOT_DIR, 'tmp')


class AppSettings(PydanticBaseSettings):
    """
    Общий класс настроек приложения
    """

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore'
    )

    database: DatabaseServiceSettings = Field(default_factory=lambda: DatabaseServiceSettings())
    sqs: SQSServiceSettings = Field(default_factory=lambda: SQSServiceSettings())
    events_polling_interval: Seconds = Field(default=...)

    def save(self) -> None:
        """
        Метод экспортирует настройки обратно в файл `.env`.

        Данный метод необходим для динамических настроек, таких как:
        `access token`, `refresh token` и других, которые могут быть обновлены
        в период работы приложения.
        """
        
        settings_dump = self.model_dump(mode='json', exclude_none=True)

        def _save_model(model_dump: dict[str, Any], prefix: str, file: TextIOWrapper) -> None:
            for key, value in model_dump.items():
                if isinstance(value, dict):
                    _save_model(
                        model_dump=value,
                        prefix=f'{prefix}{key}_',
                        file=file
                    )

                    # Вставляем отступ после вложенной модели
                    file.write('\n')
                else:
                    file.write(f'{prefix.upper()}{key.upper()}={value}\n')

        with open(
            file=str(self.model_config.get('env_file', '.env')),
            mode='w',
            encoding=self.model_config.get('env_file_encoding', 'utf8')
        ) as dotenv_file:
            _save_model(
                model_dump=settings_dump,
                prefix='',
                file=dotenv_file
            )
