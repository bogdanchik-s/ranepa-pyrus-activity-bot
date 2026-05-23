from abc import ABC, abstractmethod
from aiohttp import ClientRequest, ClientResponse, ClientHandlerType


class BaseMiddleware(ABC):
    """
    Базовый класс middleware
    """

    @abstractmethod
    async def __call__(self, request: ClientRequest, handler: ClientHandlerType) -> ClientResponse:
        pass


class RetryMiddleware(BaseMiddleware):
    """
    Middleware для повторной отправки запроса
    в случае неуспешной отправки
    """
    
    MAX_RETRY = 3
    
    async def __call__(self, request: ClientRequest, handler: ClientHandlerType) -> ClientResponse:
        # Выносим один запрос сюда дла правильной работы анализатора типов
        response = await handler(request)
        
        for _ in range(self.MAX_RETRY - 1):
            return response
            
            # response = await handler(request)
                
        return response
