from typing import NotRequired, Optional
from services.base import AuthCredentials
from pydantic import SecretStr, NonNegativeInt


class PyrusAuthCredentials(AuthCredentials):
    login: str
    person_id: NotRequired[Optional[NonNegativeInt]]
    security_key: SecretStr
    access_token: NotRequired[Optional[SecretStr]]
