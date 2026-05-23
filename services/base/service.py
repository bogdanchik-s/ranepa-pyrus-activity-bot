from abc import ABC, abstractmethod


class BaseService(ABC):
    """Базовый класс сервиса"""


    @abstractmethod
    async def start(self) -> None:
        pass

    @abstractmethod
    async def exit(self) -> None:
        pass
