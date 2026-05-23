from typing import Unpack
from common.event import Event
from services.base import ServiceRequesterMixin
from .auth import PyrusAuthCredentials
from .middlewares import AuthMiddleware


class PyrusRequesterMixin(ServiceRequesterMixin):
    """
    PyrusRequesterMixin
    """
    
    _headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'Pyrus API Python client for RANEPA'
    }


    def __init__(
        self,
        auth_credentials_changed_event: Event[PyrusAuthCredentials],
        **auth_credentials: Unpack[PyrusAuthCredentials]
    ) -> None:
        """
        Конструктур, в котором устаналиваются необходимые middlewares
        """

        auth_middleware = AuthMiddleware(
            requester=self,
            auth_credentials_changed_event=auth_credentials_changed_event,
            **auth_credentials
        )

        self._middlewares = (
            auth_middleware,
            *self._middlewares
        )
