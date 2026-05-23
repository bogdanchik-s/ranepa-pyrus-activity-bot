from abc import ABC
from pydantic import BaseModel


class BaseServiceEntity(BaseModel, ABC):
    """
    Базовая модель сущности сервиса
    """

    pass
