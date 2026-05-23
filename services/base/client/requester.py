import json
from abc import ABC
from collections.abc import Sequence
from types import GenericAlias
from typing import Self, Optional
from mimetypes import guess_all_extensions

from loguru import logger
from aiohttp import ClientSession, ClientMiddlewareType
from aiohttp.typedefs import LooseHeaders

from common.types import File
from .middlewares import RetryMiddleware
from ..models.requests import BaseServiceRequest
from ..models.responses import BaseServiceResponse, BaseServiceFileResponse, BaseServiceErrorResponse


class ServiceRequesterMixin(ABC):
    """
    Базовый класс менеджера запросов сервиса
    """

    _headers: Optional[LooseHeaders] = None
    _middlewares: Sequence[ClientMiddlewareType] = (RetryMiddleware(),)
    _client_session: ClientSession


    def __init__(self) -> None:
        """
        Конструктур, в котором устаналиваются необходимые `headers` и `middlewares`
        """

        pass

    async def send_request[ResponseType: BaseServiceResponse | BaseServiceFileResponse, ErrorResponseType: BaseServiceErrorResponse](
        self,
        request: BaseServiceRequest[ResponseType, ErrorResponseType],
        *,
        middlewares: Optional[Sequence[ClientMiddlewareType]] = None
    ) -> ResponseType | ErrorResponseType:
        """
        Метод осуществляет запрос к сервису

        Args:
            request (services.base.models.requests.BaseServiceRequest): Запрос
        
        Returns:
            BaseServiceResponse: Объект ответа на запрос, класс которого указан в `request.__response_class__`
        """

        logger.debug(f'Отправка запроса {request.__class__.__name__} на URL {request.url}...')
        
        async with self._client_session.request(request.http_method.value, request.url,
            middlewares=middlewares if middlewares is not None else (request.middleware, *self._middlewares)
        ) as client_response:
            try:
                if issubclass(request.__response_class__, BaseServiceFileResponse):
                    response_data = {'file': File(
                        mimetype=client_response.headers.get('Content-Type', ''),
                        content=await client_response.read()
                    )}
                else:
                    response_data = await client_response.json()
                    
                    # # For dev & test
                    # with open('./last_request.json', mode='w') as tmp_file:
                    #     json.dump(response_data, tmp_file, ensure_ascii=False, indent=4)
            except:
                response_data = {}
            
            if client_response.ok:
                logger.debug(f'Запрос {request.__class__.__name__} завершился успешно. Код ответа: {client_response.status}.')
                return request.__response_class__(**response_data)
            else:
                logger.debug(f'Запрос {request.__class__.__name__} завершился с ошибкой. Код ответа: {client_response.status}. Тело ответа: {await client_response.text()}')
                return request.__error_response_class__(**response_data)

    async def _create_session(self, *args, **kwargs) -> None:
        """
        Метод создает сессию с необходимыми параметрами и `middlewares`

        NOTE: Для работы метода необходим запущенный `event loop`
        """
        
        self._client_session = ClientSession(
            headers=self._headers,
            json_serialize=lambda obj: json.dumps(obj, ensure_ascii=False),
            middlewares=self._middlewares
        )

    async def _close_session(self) -> None:
        if hasattr(self, '_client_session'):
            await self._client_session.close()

    @classmethod
    def _register_requests(cls) -> None:
        for request_name, request_class in cls.__annotations__.items():
            if isinstance(request_class, GenericAlias):
                request_class = request_class.__args__[0]

            if isinstance(request_class, type) and issubclass(request_class, BaseServiceRequest):
                setattr(cls, request_name, request_class)

    def __new__(cls, *args, **kwargs) -> Self:
        cls = super().__new__(cls)
        cls._register_requests()
        return cls
