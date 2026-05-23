from services.base import AuthCredentials
from pydantic import SecretStr, NonNegativeInt


class DatabaseAuthCredentials(AuthCredentials):
    host: str
    port: NonNegativeInt
    user: str
    password: SecretStr
    name: str
