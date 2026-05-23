from abc import ABC
from typing import ClassVar, Literal
from pydantic import BaseModel
from common.types import File


class BaseServiceResponse(BaseModel, ABC):
    """
    Базовый класс ответа от сервиса
    """

    result: ClassVar[Literal['success']] = 'success'


class BaseServiceFileResponse(BaseServiceResponse, ABC):
    """
    Базовый класс файлового ответа от сервиса
    """

    file: File


class BaseServiceErrorResponse(BaseModel, ABC):
    """
    Базовый класс ошибочного ответа от сервиса
    """
    
    result: ClassVar[Literal['error']] = 'error'
