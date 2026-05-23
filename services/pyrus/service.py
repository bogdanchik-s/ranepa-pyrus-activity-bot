from typing import Unpack

from pyee.asyncio import AsyncIOEventEmitter

from common.event import Event
from services.base import BaseService, ServiceEventManagerMixin

from .client import PyrusAuthCredentials, PyrusRequesterMixin
from .models.requests import (
    GetProfileRequest,
    GetTaskRequest,
    CommentTaskRequest,
    GetFormsRequest,
    FormRegisterRequest,
    GetFileRequest,
    GetPersonRequest
)


class PyrusService(BaseService, PyrusRequesterMixin, ServiceEventManagerMixin[AsyncIOEventEmitter]):
    """
    Класс для работы с `Pyrus API`
    """

    AuthCredentialsChangedEvent: Event[PyrusAuthCredentials]
    CommentTaskEvent: Event
    NewTaskEvent: Event

    GetProfileRequest: type[GetProfileRequest]
    GetTaskRequest: type[GetTaskRequest]
    CommentTaskRequest: type[CommentTaskRequest]
    GetFormsRequest: type[GetFormsRequest]
    FormRegisterRequest: type[FormRegisterRequest]
    GetFileRequest: type[GetFileRequest]
    GetPersonRequest: type[GetPersonRequest]


    def __init__(self, **auth_credentials: Unpack[PyrusAuthCredentials]) -> None:
        super().__init__(self.AuthCredentialsChangedEvent, **auth_credentials)

    async def start(self) -> None:
        await self._create_session()

    async def exit(self) -> None:
        await self._close_session()
