from typing import Optional, Unpack
from loguru import logger
from asyncio import sleep, Lock
from http import HTTPStatus
from aiohttp import ClientHandlerType, ClientRequest, ClientResponse
from pydantic import SecretStr
from common.event import Event
from services.base import BaseMiddleware, ServiceRequesterMixin
from .auth import PyrusAuthCredentials
from ..models.requests import GetAccessTokenRequest


class AuthMiddleware(BaseMiddleware):
    """
    Middleware для авторизации
    """

    def __init__(
        self,
        requester: ServiceRequesterMixin,
        auth_credentials_changed_event: Optional[Event[PyrusAuthCredentials]] = None,
        **auth_credentials: Unpack[PyrusAuthCredentials]
    ) -> None:
        self._requester = requester
        self._auth_credentials = auth_credentials
        self._auth_credentials_changed_event = auth_credentials_changed_event
        self._lock = Lock()

    async def _get_access_token(self, expired_token: Optional[SecretStr] = None) -> SecretStr | None:
        """Метод получает новый access_token

        Returns:
            SecretStr | None: Новый `access_token` или `None` в случае неудачной попытки его получения.
        """
        
        logger.debug('Pyrus: Получение нового access_token...')

        # --- Проверяем, не заменен ли уже access_token в процессе выполнения других запросов --- #
        if self._auth_credentials.get('access_token') != expired_token:
            logger.debug('Pyrus: Access_token был получен ранее.')
            return self._auth_credentials.get('access_token')

        get_access_token_request = GetAccessTokenRequest(
            login=self._auth_credentials.get('login'),
            person_id=self._auth_credentials.get('person_id'),
            security_key=self._auth_credentials.get('security_key')
        )

        get_access_token_response = await self._requester.send_request(
            get_access_token_request,
            middlewares=(get_access_token_request.middleware,)
        )

        if get_access_token_response.result == 'success':
            logger.debug('Pyrus: Access_token успешно получен.')

            self._auth_credentials['access_token'] = get_access_token_response.access_token

            if self._auth_credentials_changed_event is not None:
                self._auth_credentials_changed_event.emit(self._auth_credentials)
            
            return self._auth_credentials.get('access_token')
        else:
            logger.debug('Pyrus: Не удалось получить access_token.')
            return None

    async def __call__(self, request: ClientRequest, handler: ClientHandlerType) -> ClientResponse:
        logger.debug('Pyrus: Авторизирование запроса...')
        
        for _ in range(2):
            access_token = self._auth_credentials.get('access_token')

            if access_token is None:
                async with self._lock:
                    access_token = await self._get_access_token()            

            request.headers['Authorization'] = f'Bearer {access_token.get_secret_value() if access_token is not None else ""}'

            response = await handler(request)

            if response.status == HTTPStatus.UNAUTHORIZED:
                async with self._lock:
                    access_token = await self._get_access_token(expired_token=access_token)
            else:
                logger.debug('Pyrus: Запрос успешно авторизирован.')
                return response

        logger.debug('Pyrus: Не удалось авторизировать запрос.')

        return response # pyright: ignore[reportPossiblyUnboundVariable]
